from flask import Blueprint, request, jsonify, current_app
from models.models import VideoProcessingTask, TaskLog, Video, db
from utils.result import Result
from utils.auth import token_required
import traceback
import os
import signal
import psutil
import threading
from datetime import datetime

# 导入视频处理线程池
from utils.video_processing_pool import video_processing_pool

task_logs_bp = Blueprint('task_logs', __name__)

@task_logs_bp.route('/list', methods=['GET'])
@token_required
def list_tasks():
    """获取任务列表"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 10))
        status = request.args.get('status', None)
        
        query = VideoProcessingTask.query
        
        # 根据状态筛选
        if status:
            query = query.filter(VideoProcessingTask.status == status)
            
        # 关联视频信息
        tasks_with_video = query.join(Video, VideoProcessingTask.video_id == Video.id) \
            .add_columns(
                VideoProcessingTask.id, 
                VideoProcessingTask.task_id,
                VideoProcessingTask.video_id,
                VideoProcessingTask.status,
                VideoProcessingTask.progress,
                VideoProcessingTask.start_time,
                VideoProcessingTask.end_time,
                VideoProcessingTask.error_message,
                Video.title.label('video_title'),
                Video.cover_url.label('video_cover')
            )
            
        # 按开始时间倒序排序
        tasks_with_video = tasks_with_video.order_by(VideoProcessingTask.start_time.desc())
        
        # 分页
        pagination = tasks_with_video.paginate(page=page, per_page=size, error_out=False)
        total = pagination.total
          # 格式化结果
        tasks_list = []
        for task in pagination.items:
            task_dict = {
                'id': task.id,
                'task_id': task.task_id,
                'video_id': task.video_id,
                'status': task.status,
                'progress': task.progress,
                'start_time': task.start_time.isoformat() if task.start_time else None,
                'end_time': task.end_time.isoformat() if task.end_time else None,
                'error_message': task.error_message,
                'video_title': task.video_title,
                'video_cover': os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{task.video_cover}" or task.video_cover
            }
            tasks_list.append(task_dict)
        
        # 获取线程池状态信息
        pool_status = {
            'active_tasks': video_processing_pool.get_active_tasks_count(),
            'pending_tasks': video_processing_pool.get_pending_tasks_count(),
            'max_workers': video_processing_pool.max_workers
        }
        
        return jsonify(Result.success({
            'list': tasks_list,
            'total': total,
            'page': page,
            'size': size,
            'pool_status': pool_status
        }))
        
    except Exception as e:
        current_app.logger.error(f"获取任务列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取任务列表失败: {str(e)}"))

@task_logs_bp.route('/logs/<task_id>', methods=['GET'])
@token_required
def get_task_logs(task_id):
    """获取特定任务的日志"""
    try:
        # 首先检查任务是否存在
        task = VideoProcessingTask.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify(Result.error(404, "找不到指定的任务"))
        
        # 获取该任务的所有日志，按时间正序排列
        logs = TaskLog.query.filter_by(task_id=task_id) \
            .order_by(TaskLog.timestamp.asc()) \
            .all()
            
        # 将日志转换为字典
        logs_list = [log.to_dict() for log in logs]
        
        # 获取任务状态
        task_info = {
            'id': task.id,
            'task_id': task.task_id,
            'video_id': task.video_id,
            'status': task.status,
            'progress': task.progress,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'error_message': task.error_message
        }
        
        return jsonify(Result.success({
            'task': task_info,
            'logs': logs_list
        }))
        
    except Exception as e:
        current_app.logger.error(f"获取任务日志失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取任务日志失败: {str(e)}"))

@task_logs_bp.route('/task/<task_id>', methods=['GET'])
@token_required
def get_task_info(task_id):
    """获取特定任务的信息"""
    try:
        # 检查任务是否存在
        task = VideoProcessingTask.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify(Result.error(404, "找不到指定的任务"))
            
        # 关联视频信息
        video = Video.query.get(task.video_id)
        
        # 返回任务信息
        task_info = {
            'id': task.id,
            'task_id': task.task_id,
            'video_id': task.video_id,
            'status': task.status,
            'progress': task.progress,
            'start_time': task.start_time.isoformat() if task.start_time else None,
            'end_time': task.end_time.isoformat() if task.end_time else None,
            'error_message': task.error_message,
            'video_title': video.title if video else "未知视频",
            'video_cover': os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" if video else None
        }
        
        return jsonify(Result.success(task_info))
        
    except Exception as e:
        current_app.logger.error(f"获取任务信息失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取任务信息失败: {str(e)}"))

@task_logs_bp.route('/task/<task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    """删除指定任务及其日志，如果任务正在处理中则终止处理线程"""
    try:
        # 查找任务
        task = VideoProcessingTask.query.filter_by(task_id=task_id).first()
        if not task:
            return jsonify(Result.error(404, "找不到指定的任务"))
            
        # 如果任务正在处理中，尝试终止对应的线程
        if task.status == 'processing':
            try:
                # 尝试通过线程池停止任务
                stopped = video_processing_pool.stop_task(task_id)
                
                if stopped:
                    current_app.logger.info(f"已通过线程池停止任务 {task_id}")
                    
                    # 添加操作日志
                    log = TaskLog(
                        task_id=task_id,
                        video_id=task.video_id,
                        log_level="warning",
                        message=f"用户请求终止任务，已设置停止标志"
                    )
                    db.session.add(log)
                    
                    # 更新任务状态
                    task.status = 'cancelled'
                    task.error_message = '任务被手动终止'
                    task.end_time = datetime.now()
                else:
                    # 如果在线程池中找不到，检查应用的线程字典
                    if hasattr(current_app, 'PROCESSING_THREADS') and task_id in current_app.PROCESSING_THREADS:
                        thread_info = current_app.PROCESSING_THREADS[task_id]
                        
                        # 设置停止标志
                        if 'stop_flag' in thread_info:
                            thread_info['stop_flag'].set()
                            current_app.logger.info(f"已设置任务 {task_id} 的停止标志，线程ID: {thread_info.get('thread_id')}")
                            
                            # 更新任务状态
                            task.status = 'cancelled'
                            task.error_message = '任务被手动终止'
                            task.end_time = datetime.now()
                            
                            # 添加操作日志
                            log = TaskLog(
                                task_id=task_id,
                                video_id=task.video_id,
                                log_level="warning",
                                message=f"用户请求终止任务，已设置停止标志"
                            )
                            db.session.add(log)
                    else:
                        # 如果在线程池和全局字典中都找不到，只更新任务状态
                        current_app.logger.warning(f"任务 {task_id} 状态为处理中，但在活动线程中未找到")
                        task.status = 'cancelled'
                        task.error_message = '任务被手动终止，但无法找到处理线程'
                        task.end_time = datetime.now()
                        
                        # 添加操作日志
                        log = TaskLog(
                            task_id=task_id,
                            video_id=task.video_id,
                            log_level="warning",
                            message=f"用户请求终止任务，但未找到对应的处理线程"
                        )
                        db.session.add(log)
            except Exception as e:
                current_app.logger.error(f"尝试终止任务线程时出错: {str(e)}")
                # 添加错误日志
                log = TaskLog(
                    task_id=task_id,
                    video_id=task.video_id,
                    log_level="error",
                    message=f"尝试终止任务时发生错误: {str(e)}"
                )
                db.session.add(log)
        else:
            # 如果任务不是处理中状态，直接标记为取消状态
            task.status = 'cancelled'
            task.error_message = '任务被手动删除'
            task.end_time = datetime.now() if not task.end_time else task.end_time
            
        # 不删除任务日志，只添加一条删除操作的日志
        log = TaskLog(
            task_id=task_id,
            video_id=task.video_id,
            log_level="info",
            message="用户删除了任务"
        )
        db.session.add(log)
        
        # 提交更改
        db.session.commit()
        
        return jsonify(Result.success(None, "任务已成功取消"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除任务失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"删除任务失败: {str(e)}"))

@task_logs_bp.route('/pool-status', methods=['GET'])
@token_required
def get_pool_status():
    """获取视频处理线程池的状态"""
    try:
        status = {
            'active_tasks': video_processing_pool.get_active_tasks_count(),
            'pending_tasks': video_processing_pool.get_pending_tasks_count(),
            'max_workers': video_processing_pool.max_workers,
            'is_full': video_processing_pool.get_active_tasks_count() >= video_processing_pool.max_workers
        }
        
        # 获取正在处理的任务信息
        active_tasks = []
        for task_id, task_info in video_processing_pool.current_tasks.items():
            # 查找任务记录
            task = VideoProcessingTask.query.filter_by(task_id=task_id).first()
            if task:
                # 获取视频信息
                video = Video.query.get(task.video_id)
                active_tasks.append({
                    'task_id': task_id,
                    'video_id': str(task.video_id),
                    'video_title': video.title if video else "未知视频",
                    'start_time': task_info['start_time'].isoformat(),
                    'duration': (datetime.now() - task_info['start_time']).total_seconds(),
                    'progress': task.progress
                })
        
        status['active_task_details'] = active_tasks
        
        return jsonify(Result.success(status))
    except Exception as e:
        current_app.logger.error(f"获取线程池状态失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取线程池状态失败: {str(e)}"))
