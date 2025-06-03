from flask import Blueprint, request, jsonify, current_app, session
from utils.result import Result
from utils.file_util import allowed_file, save_file, allowed_video_file, allowed_document_file
from datetime import datetime
from models.models import db, Document, Video, Users
import pandas as pd
import io
import re
from werkzeug.security import generate_password_hash
import os
import subprocess
import json
import uuid
import threading
from threading import Thread
import dotenv
dotenv.load_dotenv()
# 创建一个全局字典来存储线程信息和停止标志
PROCESSING_THREADS = {}

# 导入视频处理任务
from tasks.video_processor.main_processor import process_video_task
from models.models import VideoProcessingTask
from utils.auth import get_current_user_id as jwt_get_user_id
from utils.auth import token_required
from utils.video_processing_pool import video_processing_pool

upload_bp = Blueprint('uploads', __name__)

def get_current_user_id():
    """获取当前登录用户ID"""
    # 尝试从JWT中获取用户ID
    user_id = jwt_get_user_id()
    if user_id:
        return user_id
        
    # 如果JWT认证失败，尝试从session获取
    user_id = session.get('user_id')
    return user_id

def is_teacher_or_admin(user_id):
    """检查用户是否为教师或管理员"""
    if not user_id:
        return False
    
    user = Users.query.get(user_id)
    if not user:
        return False
        
    return user.role in ['teacher', 'admin']

@upload_bp.route('/image', methods=['POST'])
def upload_image():
    """
    上传图片接口，需要教师或管理员权限
    """
    try:
        # 检查权限
        user_id = get_current_user_id()
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
        
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_file(file.filename):
            return jsonify(Result.error(400, "不支持的文件格式，请上传图片文件"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='image')
        
        # 返回文件信息
        return jsonify(Result.success({
            "imageUrl": file_path
        }, "图片上传成功"))
        
    except Exception as e:
        current_app.logger.error(f"图片上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/document', methods=['POST'])
def upload_document():
    """
    上传课件文档接口，需要教师或管理员权限
    """
    try:
        # 检查权限
        user_id = get_current_user_id()
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
        
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        # 获取课程ID
        course_id = request.form.get('courseId')
        if not course_id:
            return jsonify(Result.error(400, "未提供课程ID"))
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_document_file(file.filename):
            return jsonify(Result.error(400, "不支持的文档格式"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='document')
        
        # 获取文件大小和类型
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # 重置文件指针
        file_type = file.filename.split('.')[-1].lower()
        
        # 创建文档记录并保存到数据库
        document = Document(
            title=file.filename,
            file_url=file_path,
            file_type=file_type,
            file_size=file_size,
            course_id=int(course_id),
            upload_time=datetime.now(),
            is_deleted=False
        )
        
        db.session.add(document)
        db.session.commit()
        
        # 返回文件信息
        return jsonify(Result.success({
            "documentId": document.id,
            "documentUrl": document.file_url,
            "documentName": document.title,
            "documentType": document.file_type,
            "size": document.file_size
        }, "课件上传成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"文档上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/student_list', methods=['POST'])
def upload_student_list():
    """
    上传学生名单接口
    """
    try:
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否为Excel或CSV
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            return jsonify(Result.error(400, "请上传Excel或CSV格式的文件"))
        
        # 解析Excel/CSV文件
        invalid_records = []
        preview_data = []
        
        # 读取文件内容
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
            
        # 验证必要列是否存在
        required_columns = ['studentId', 'name', 'email']
        for col in required_columns:
            if col not in df.columns:
                return jsonify(Result.error(400, f"文件缺少必要列: {col}"))
        
        # 验证每行数据
        valid_students = []
        for index, row in df.iterrows():
            student = {
                'studentId': str(row['studentId']),
                'name': str(row['name']),
                'email': str(row['email'])
            }
            
            # 检查邮箱格式
            if not re.match(r"[^@]+@[^@]+\.[^@]+", student['email']):
                invalid_records.append({
                    "row": index + 2,  # +2因为Excel从1开始，且有表头
                    "reason": "邮箱格式错误"
                })
                continue
                
            # 检查学号是否已存在
            existing_user = Users.query.filter_by(
                username=student['studentId'], 
                is_deleted=False
            ).first()
            
            if existing_user:
                invalid_records.append({
                    "row": index + 2,
                    "reason": "学号已存在"
                })
                continue
                
            # 检查邮箱是否已存在
            existing_email = Users.query.filter_by(
                email=student['email'], 
                is_deleted=False
            ).first()
            
            if existing_email:
                invalid_records.append({
                    "row": index + 2,
                    "reason": "邮箱已被使用"
                })
                continue
            
            valid_students.append(student)
            
            # 添加到预览数据（最多显示5条）
            if len(preview_data) < 5:
                preview_data.append(student)
        
        # 返回解析结果
        return jsonify(Result.success({
            "totalCount": len(df),
            "validCount": len(valid_students),
            "invalidRecords": invalid_records,
            "previewData": preview_data,
            "validStudents": valid_students  # 传递有效学生列表供后续导入使用
        }, "学生名单解析成功"))
        
    except Exception as e:
        current_app.logger.error(f"学生名单上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/course_video', methods=['POST'])
def upload_course_video():
    """
    上传教学视频资源接口
    """
    try:
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
          # 获取附加参数
        course_id = request.form.get('courseId')
        title = request.form.get('title')
        description = request.form.get('description', '')
        
        # 获取处理步骤选择参数
        processing_steps_str = request.form.get('processingSteps')
        preview_mode = request.form.get('previewMode', 'false').lower() == 'true'
        
        # 解析处理步骤
        processing_steps = None
        if processing_steps_str:
            try:
                processing_steps = json.loads(processing_steps_str)
                if not isinstance(processing_steps, list):
                    return jsonify(Result.error(400, "processingSteps必须是数组格式"))
                
                # 验证步骤名称
                valid_steps = ['keyframes', 'ocr', 'asr', 'vector', 'summary']
                for step in processing_steps:
                    if step not in valid_steps:
                        return jsonify(Result.error(400, f"无效的处理步骤: {step}"))
            except json.JSONDecodeError:
                return jsonify(Result.error(400, "processingSteps格式错误"))
        
        json_sub = None
        
        if not all([course_id, title]):
            return jsonify(Result.error(400, "缺少必要参数"))
        
        file = request.files['file']
        if 'json_sub' in request.files:
            json_sub = request.files['json_sub']
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_video_file(file.filename):
            return jsonify(Result.error(400, "不支持的视频格式"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='video')
        
        # 如果有字幕文件，保存同名json文件
        if json_sub:
            # 获取视频文件名（不含扩展名）
            video_filename = os.path.splitext(os.path.basename(file_path))[0]
            # 构造json文件路径
            json_dir = os.path.dirname(file_path)
            json_path = os.path.join(json_dir, f"{video_filename}.json")
            
            # 保存json文件
            actual_json_path = os.path.join(os.getcwd(), json_path.lstrip('/'))
            print(actual_json_path)
            json_sub.save(actual_json_path)
        
        # 实际路径计算
        actual_file_path = os.path.join(os.getcwd(), file_path.lstrip('/'))
        
        # 使用ffmpeg获取视频时长
        try:
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-show_entries', 'format=duration', 
                '-of', 'json', 
                actual_file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(result.stdout)
            duration = int(float(data['format']['duration']))
        except (subprocess.SubprocessError, json.JSONDecodeError, KeyError) as e:
            current_app.logger.error(f"获取视频时长失败: {str(e)}")
            # 如果ffmpeg命令失败，使用默认时长
            duration = 1800  # 默认30分钟
        
        # 生成视频封面图
        try:
            # 确保目录存在
            thumb_dir = 'temp_img'
            if not os.path.exists(thumb_dir):
                os.makedirs(thumb_dir)
                
            thumbnail_filename = f"{uuid.uuid4().hex}_thumb.jpg"
            thumbnail_path = os.path.join(thumb_dir, thumbnail_filename)
            
            # 使用ffmpeg抓取视频第5秒的帧作为封面
            cmd = [
                'ffmpeg',
                '-i', actual_file_path,
                '-ss', '00:00:05',
                '-vframes', '1',
                '-vf', 'scale=320:-1',
                thumbnail_path
            ]
            subprocess.run(cmd, capture_output=True)
            
            cover_url = f"/temp_img/{thumbnail_filename}"
        except subprocess.SubprocessError as e:
            current_app.logger.error(f"生成视频封面失败: {str(e)}")
            # 如果生成封面失败，使用默认封面
            cover_url = "/temp_img/default_video_cover.jpg"
        
        # 创建视频记录并保存到数据库
        video = Video(
            title=title,
            description=description,
            cover_url=cover_url,
            video_url=file_path,
            duration=duration,
            course_id=(course_id),
            view_count=0,
            comment_count=0,
            upload_time=datetime.now(),
            is_deleted=False
        )
        
        db.session.add(video)
        db.session.commit()          # 创建视频处理任务
        try:
            task_id = f"task-{uuid.uuid4().hex[:8]}"
            
            # 根据preview_mode设置处理类型
            processing_type = "preview" if preview_mode else "all"
            if processing_steps:
                processing_type = f"custom_{','.join(processing_steps)}"
            
            task = VideoProcessingTask(
                video_id=video.id,
                task_id=task_id,
                status="pending",
                processing_type=processing_type,
                progress=0.0,
                start_time=datetime.now()
            )
            db.session.add(task)
            db.session.commit()
            
            # 提交任务到线程池处理，不阻塞HTTP响应
            # 使用新的submit_task_with_params方法支持处理步骤和预览模式
            if processing_steps is not None or preview_mode:
                task_id, stop_flag = video_processing_pool.submit_task_with_params(
                    current_app._get_current_object(), 
                    video.id, 
                    process_video_task,
                    processing_steps=processing_steps,
                    preview_mode=preview_mode
                )
            else:
                # 向后兼容：如果没有指定新参数，使用默认处理
                task_id, stop_flag = video_processing_pool.submit_task(
                    current_app._get_current_object(), 
                    video.id, 
                    process_video_task
                )
            
            # 更新任务ID（如果线程池生成了新的ID）
            if task.task_id != task_id:
                task.task_id = task_id
                db.session.commit()
            
        except Exception as e:
            # 如果创建任务失败，记录日志但不中断上传
            current_app.logger.error(f"创建视频处理任务失败: {str(e)}")
            task_id = "task-manual"
          # 返回视频信息
        return jsonify(Result.success({
            "videoId": video.id,
            "videoUrl": video.video_url,
            "title": video.title,
            "description": video.description,
            "duration": video.duration,
            "courseId": video.course_id,
            "processingStatus": "pending",
            "processingSteps": processing_steps,
            "previewMode": preview_mode,
            "uploadTime": video.upload_time.isoformat(),
            "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
            "taskId": task_id
        }, "教学视频上传成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"视频上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))

@upload_bp.route('/avatar', methods=['POST'])
@token_required
def upload_avatar():
    """
    上传用户头像接口
    """
    try:
        # 获取当前用户ID
        user_id = request.user.get('user_id')
        if not user_id:
            return jsonify(Result.error(401, "未登录"))
        
        # 检查是否有文件部分
        if 'file' not in request.files:
            return jsonify(Result.error(400, "未找到上传文件"))
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器可能会发送一个没有文件名的空文件部分
        if file.filename == '':
            return jsonify(Result.error(400, "未选择文件"))
        
        # 检查文件类型是否允许
        if not allowed_file(file.filename):
            return jsonify(Result.error(400, "不支持的文件格式，请上传图片文件"))
        
        # 保存文件并获取保存路径
        file_path = save_file(file, file_type='avatar')
        
        # 更新用户的头像URL
        user = Users.query.get(user_id)
        if not user:
            return jsonify(Result.error(404, "用户不存在"))
            
        user.avatar = file_path
        db.session.commit()
        
        # 返回文件信息
        return jsonify(Result.success({
            "avatar": file_path
        }, "头像上传成功"))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"头像上传错误: {str(e)}")
        return jsonify(Result.error(500, f"服务器错误: {str(e)}"))