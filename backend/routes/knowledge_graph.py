"""
知识图谱相关API路由
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import uuid
from datetime import datetime

from utils.auth import token_required
from models.models import (
    Video, db, Course, Keyword, VideoKeyword, CourseKeyword, 
    KeywordRelation, KnowledgeGraphProcessingTask
)

knowledge_graph_bp = Blueprint('knowledge_graph', __name__)



@knowledge_graph_bp.route('/api/knowledge-graph/generate', methods=['POST'])
@token_required
def generate_knowledge_graph():
    """触发知识图谱生成"""
    try:
        data = request.get_json()
        course_id = data.get('courseId')
        #force_regenerate = data.get('forceRegenerate', False)
        force_regenerate = True
        incremental = data.get('incremental', True)  # 默认启用增量处理
        
        if not course_id:
            return jsonify({
                'code': 400,
                'msg': '课程ID不能为空',
                'data': None
            }), 400
        
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
          # 检查是否有正在进行的任务
        existing_task = KnowledgeGraphProcessingTask.query.filter_by(
            course_id=course_id,
            status='processing'
        ).first()
        
        if existing_task and not force_regenerate:
            return jsonify({
                'code': 409,
                'msg': '该课程的知识图谱正在生成中',
                'data': existing_task.to_dict()
            }), 409
        elif force_regenerate:
            # 如果有正在进行的任务且force_regenerate为True，更新任务状态
            #删除对应课程的关键词和关系数据
            # 获取该课程下的所有视频ID列表
            video_ids = [row[0] for row in db.session.query(Video.id).filter(Video.course_id == course_id).all()]
            
            # 获取该课程下的所有视频关键词ID
            video_keyword_ids = [row[0] for row in db.session.query(VideoKeyword.keyword_id).filter(VideoKeyword.video_id.in_(video_ids)).all()]
            # 删除关键词关系
            if video_keyword_ids:
                db.session.query(KeywordRelation).filter(
                    (KeywordRelation.source_keyword_id.in_(video_keyword_ids)) | 
                    (KeywordRelation.target_keyword_id.in_(video_keyword_ids))
                ).delete(synchronize_session=False)

            db.session.commit()
        
        # 异步触发知识图谱生成
        from utils.knowledge_graph_processing_pool import knowledge_graph_processing_pool
        from tasks.knowledge_graph_processor import process_knowledge_graph_task
          # 创建知识图谱处理任务
        task_id = f"kg-task-{uuid.uuid4().hex[:8]}"
        task_type = 'full_knowledge_graph' if force_regenerate or not incremental else 'incremental_knowledge_graph'
        task = KnowledgeGraphProcessingTask(
            course_id=course_id,
            task_type=task_type,
            status="pending",
            start_time=datetime.now()
        )
        db.session.add(task)
        db.session.commit()
          # 提交任务到线程池处理，不阻塞HTTP响应
        print((
            current_app._get_current_object(), 
            course_id, 
            process_knowledge_graph_task,
            force_regenerate,
            incremental
        ))
        pool_task_id, stop_flag = knowledge_graph_processing_pool.submit_task(
            current_app._get_current_object(), 
            course_id, 
            process_knowledge_graph_task,
            force_regenerate,
            incremental
        )
        
        # 更新任务ID（如果线程池生成了新的ID）
        if task.id != pool_task_id:
            # 这里使用数据库自动生成的UUID作为task_id
            pass
        
        return jsonify({
            'code': 200,
            'msg': '知识图谱生成任务已启动',
            'data': {
                "taskId": str(task.id),
                "pendingTasks": knowledge_graph_processing_pool.get_pending_tasks_count(),
                "activeTasks": knowledge_graph_processing_pool.get_active_tasks_count()
            }
        })
            
    except Exception as e:
        
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>', methods=['GET'])
@token_required
def get_course_knowledge_graph(course_id):
    """获取课程知识图谱"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
        
        # 获取课程关键词
        course_keywords = db.session.query(
            Keyword, CourseKeyword
        ).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        ).all()
        
        # 构建节点数据
        nodes = []
        node_categories = []
        category_map = {}
        
        # 添加分类到map
        categories = ['core_concept', 'main_module', 'specific_point']
        category_names = ['核心概念', '主要模块', '具体知识点']
        
        for i, (cat, name) in enumerate(zip(categories, category_names)):
            category_map[cat] = i
            node_categories.append({'name': name})
        
        # 构建节点
        keyword_id_map = {}
        for keyword, course_keyword in course_keywords:
            # 根据视频数量和权重计算节点大小
            symbol_size = max(30, min(80, 30 + course_keyword.video_count * 5 + course_keyword.avg_weight * 20))
            
            node = {
                'id': str(keyword.id),
                'name': keyword.name,
                'category': category_map.get(keyword.category, 2),
                'symbolSize': symbol_size,
                'video_count': course_keyword.video_count,
                'avg_weight': round(course_keyword.avg_weight, 2),
                'description': keyword.description or f"{keyword.name}相关知识点"
            }
            nodes.append(node)
            keyword_id_map[keyword.id] = keyword.name
        
        # 获取关键词关系
        keyword_ids = list(keyword_id_map.keys())
        relations = KeywordRelation.query.filter(
            KeywordRelation.source_keyword_id.in_(keyword_ids),
            KeywordRelation.target_keyword_id.in_(keyword_ids)
        ).all()
        
        # 构建边数据
        links = []
        for relation in relations:
            link = {
                'source': str(relation.source_keyword_id),
                'target': str(relation.target_keyword_id),
                'relation_type': relation.relation_type,
                'strength': relation.strength,
                'description': relation.description,
                'lineStyle': {
                    'width': max(1, relation.strength * 3),  # 根据强度设置线宽
                    'opacity': max(0.3, relation.strength)   # 根据强度设置透明度
                }
            }
            links.append(link)
        
        # 构建返回数据
        graph_data = {
            'nodes': nodes,
            'links': links,
            'categories': node_categories,
            'course_info': {
                'id': str(course.id),
                'name': course.name,
                'description': course.description
            },
            'statistics': {
                'total_keywords': len(nodes),
                'total_relations': len(links),
                'core_concepts': len([n for n in nodes if n['category'] == 0]),
                'main_modules': len([n for n in nodes if n['category'] == 1]),
                'specific_points': len([n for n in nodes if n['category'] == 2])
            }
        }
        
        return jsonify({
            'code': 200,
            'msg': '获取知识图谱成功',
            'data': graph_data
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/platform', methods=['GET'])
@token_required
def get_platform_knowledge_graph():
    """获取平台级知识图谱"""
    try:
        # 批量查询所有需要的数据
        # 1. 获取所有关键词
        all_keywords = Keyword.query.all()
        keyword_ids = [kw.id for kw in all_keywords]
        
        # 2. 批量查询课程关键词统计
        course_stats = db.session.query(
            CourseKeyword.keyword_id,
            db.func.count(CourseKeyword.course_id).label('course_count')
        ).filter(
            CourseKeyword.keyword_id.in_(keyword_ids)
        ).group_by(CourseKeyword.keyword_id).all()
        
        # 3. 批量查询视频关键词统计
        video_stats = db.session.query(
            VideoKeyword.keyword_id,
            db.func.count(VideoKeyword.video_id).label('video_count')
        ).filter(
            VideoKeyword.keyword_id.in_(keyword_ids)
        ).group_by(VideoKeyword.keyword_id).all()
        
        # 4. 批量查询所有关键词关系
        all_relations = KeywordRelation.query.filter(
            KeywordRelation.source_keyword_id.in_(keyword_ids),
            KeywordRelation.target_keyword_id.in_(keyword_ids)
        ).all()
        
        # 构建统计字典
        course_count_map = {stat.keyword_id: stat.course_count for stat in course_stats}
        video_count_map = {stat.keyword_id: stat.video_count for stat in video_stats}
        
        # 构建节点数据
        nodes = []
        node_categories = []
        category_map = {}
        
        # 添加分类
        categories = ['core_concept', 'main_module', 'specific_point']
        category_names = ['核心概念', '主要模块', '具体知识点']
        
        for i, (cat, name) in enumerate(zip(categories, category_names)):
            category_map[cat] = i
            node_categories.append({'name': name})
        
        # 构建节点
        keyword_id_map = {}
        for keyword in all_keywords:
            course_count = course_count_map.get(keyword.id, 0)
            video_count = video_count_map.get(keyword.id, 0)
            
            # 根据课程数量和视频数量计算节点大小
            symbol_size = max(25, min(100, 25 + course_count * 10 + video_count * 2))
            
            node = {
                'id': str(keyword.id),
                'name': keyword.name,
                'category': category_map.get(keyword.category, 2),
                'symbolSize': symbol_size,
                'course_count': course_count,
                'video_count': video_count,
                'description': keyword.description or f"{keyword.name}相关知识点"
            }
            nodes.append(node)
            keyword_id_map[keyword.id] = keyword.name
        
        # 构建边数据
        links = []
        for relation in all_relations:
            link = {
                'source': str(relation.source_keyword_id),
                'target': str(relation.target_keyword_id),
                'relation_type': relation.relation_type,
                'strength': relation.strength,
                'description': relation.description,
                'lineStyle': {
                    'width': max(1, relation.strength * 3),
                    'opacity': max(0.3, relation.strength)
                }
            }
            links.append(link)
        
        # 构建返回数据
        graph_data = {
            'nodes': nodes,
            'links': links,
            'categories': node_categories,
            'statistics': {
                'total_keywords': len(nodes),
                'total_relations': len(links),
                'core_concepts': len([n for n in nodes if n['category'] == 0]),
                'main_modules': len([n for n in nodes if n['category'] == 1]),
                'specific_points': len([n for n in nodes if n['category'] == 2])
            }
        }
        
        return jsonify({
            'code': 200,
            'msg': '获取平台知识图谱成功',
            'data': graph_data
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keyword/<keyword_id>/videos', methods=['GET'])
@token_required
def get_keyword_related_videos(keyword_id):
    """获取关键词相关的视频"""
    try:
        # 验证关键词是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '关键词不存在',
                'data': None
            }), 404
        
        # 获取关键词相关的视频
        try:
            video_keywords = db.session.query(
                VideoKeyword, Video, Course
            ).join(
                Video, VideoKeyword.video_id == Video.id
            ).join(
                Course, Video.course_id == Course.id
            ).filter(
                VideoKeyword.keyword_id == keyword_id,
                Video.is_deleted == False
            ).order_by(VideoKeyword.weight.desc()).all()
            
        except Exception as e:
            print(f"查询视频时出错: {str(e)}")  # 添加日志
            raise
        
        videos = []
        for vk, video, course in video_keywords:
            video_data = {
                'id': str(video.id),
                'title': video.title,
                'description': video.description,
                'cover_url': video.cover_url,
                'duration': video.duration,
                'upload_time': video.upload_time.strftime('%Y-%m-%d %H:%M:%S'),
                'view_count': video.view_count,
                'weight': round(vk.weight, 2),
                'course': {
                    'id': str(course.id),
                    'name': course.name
                }
            }
            videos.append(video_data)
        
        return jsonify({
            'code': 200,
            'msg': '获取关键词相关视频成功',
            'data': {
                'keyword': keyword.to_dict(),
                'videos': videos,
                'total': len(videos)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/task/<task_id>', methods=['GET'])
@token_required
def get_task_status(task_id):
    """获取知识图谱生成任务状态"""
    try:
        task = KnowledgeGraphProcessingTask.query.get(task_id)
        if not task:
            return jsonify({
                'code': 404,
                'msg': '任务不存在',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'msg': '获取任务状态成功',
            'data': task.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>/task', methods=['GET'])
@token_required
def get_course_task_status(course_id):
    """获取课程最新的知识图谱任务状态"""
    try:
        # 获取该课程最新的任务
        task = KnowledgeGraphProcessingTask.query.filter_by(
            course_id=course_id
        ).order_by(KnowledgeGraphProcessingTask.create_time.desc()).first()
        
        if not task:
            return jsonify({
                'code': 404,
                'msg': '未找到相关任务',
                'data': None
            }), 404
        
        return jsonify({
            'code': 200,
            'msg': '获取任务状态成功',
            'data': task.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500


@knowledge_graph_bp.route('/api/knowledge-graph/pool-status', methods=['GET'])
@token_required
def get_pool_status():
    """获取知识图谱处理线程池的状态"""
    try:
        from utils.knowledge_graph_processing_pool import knowledge_graph_processing_pool
        
        status = {
            'active_tasks': knowledge_graph_processing_pool.get_active_tasks_count(),
            'pending_tasks': knowledge_graph_processing_pool.get_pending_tasks_count(),
            'max_workers': knowledge_graph_processing_pool.max_workers,
            'is_full': knowledge_graph_processing_pool.get_active_tasks_count() >= knowledge_graph_processing_pool.max_workers
        }
        
        # 获取正在处理的任务信息
        active_tasks = []
        for task_id, task_info in knowledge_graph_processing_pool.current_tasks.items():
            # 查找任务记录
            task = KnowledgeGraphProcessingTask.query.filter_by(course_id=task_info['course_id']).order_by(
                KnowledgeGraphProcessingTask.create_time.desc()
            ).first()
            if task:
                # 获取课程信息
                course = Course.query.get(task.course_id)
                active_tasks.append({
                    'task_id': task_id,
                    'course_id': str(task.course_id),
                    'course_title': course.title if course else "未知课程",
                    'start_time': task_info['start_time'].isoformat(),
                    'progress': task.progress if task else 0
                })
        
        status['active_tasks_detail'] = active_tasks
        
        return jsonify({
            'code': 200,
            'msg': '获取线程池状态成功',
            'data': status
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/video/<video_id>/keywords', methods=['GET'])
@token_required
def get_video_keywords(video_id):
    """获取视频的所有关键词"""
    try:
        # 验证视频是否存在
        video = Video.query.get(video_id)
        if not video:
            return jsonify({
                'code': 404,
                'msg': '视频不存在',
                'data': None
            }), 404
        
        # 获取视频关键词
        video_keywords = db.session.query(
            Keyword, VideoKeyword
        ).join(VideoKeyword).filter(
            VideoKeyword.video_id == video_id
        ).order_by(VideoKeyword.weight.desc()).all()
        
        # 构建返回数据
        keywords_data = []
        for keyword, video_keyword in video_keywords:
            keywords_data.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'weight': video_keyword.weight,
                'create_time': video_keyword.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'code': 200,
            'msg': '获取视频关键词成功',
            'data': {
                'video_info': {
                    'id': str(video.id),
                    'title': video.title,
                    'description': video.description
                },
                'keywords': keywords_data,
                'total_count': len(keywords_data)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>/keywords', methods=['GET'])
@token_required
def get_course_keywords_detailed(course_id):
    """获取课程的所有关键词（带统计信息）"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
        
        # 获取请求参数
        category = request.args.get('category')  # 可选：过滤特定分类
        limit = request.args.get('limit', type=int)  # 可选：限制返回数量
        
        # 构建查询
        query = db.session.query(
            Keyword, CourseKeyword
        ).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        )
        
        if category:
            query = query.filter(Keyword.category == category)
        
        # 按视频数量和平均权重排序
        query = query.order_by(
            CourseKeyword.video_count.desc(),
            CourseKeyword.avg_weight.desc()
        )
        
        if limit:
            query = query.limit(limit)
        
        course_keywords = query.all()
        
        # 构建返回数据
        keywords_data = []
        for keyword, course_keyword in course_keywords:
            keywords_data.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'video_count': course_keyword.video_count,
                'avg_weight': round(course_keyword.avg_weight, 3),
                'importance_score': round(course_keyword.video_count * course_keyword.avg_weight, 3),
                'create_time': course_keyword.create_time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 统计信息
        category_stats = db.session.query(
            Keyword.category,
            db.func.count(Keyword.id).label('count')
        ).join(CourseKeyword).filter(
            CourseKeyword.course_id == course_id
        ).group_by(Keyword.category).all()
        
        return jsonify({
            'code': 200,
            'msg': '获取课程关键词成功',
            'data': {
                'course_info': {
                    'id': str(course.id),
                    'name': course.name,
                    'description': course.description
                },
                'keywords': keywords_data,
                'total_count': len(keywords_data),
                'category_stats': {cat: count for cat, count in category_stats}
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/keyword/<keyword_id>/usage', methods=['GET'])
@token_required
def get_keyword_usage(keyword_id):
    """获取关键词的使用情况（在哪些视频和课程中出现）"""
    try:
        # 验证关键词是否存在
        keyword = Keyword.query.get(keyword_id)
        if not keyword:
            return jsonify({
                'code': 404,
                'msg': '关键词不存在',
                'data': None
            }), 404
        
        # 获取关键词在视频中的使用情况
        video_usage = db.session.query(
            VideoKeyword, Video, Course
        ).join(Video).join(Course).filter(
            VideoKeyword.keyword_id == keyword_id,
            Video.is_deleted == False
        ).order_by(VideoKeyword.weight.desc()).all()
        
        videos_data = []
        course_map = {}
        
        for vk, video, course in video_usage:
            video_data = {
                'id': str(video.id),
                'title': video.title,
                'duration': video.duration,
                'weight': vk.weight,
                'course_id': str(course.id),
                'course_name': course.name
            }
            videos_data.append(video_data)
            
            # 统计课程信息
            if str(course.id) not in course_map:
                course_map[str(course.id)] = {
                    'id': str(course.id),
                    'name': course.name,
                    'video_count': 0,
                    'total_weight': 0
                }
            course_map[str(course.id)]['video_count'] += 1
            course_map[str(course.id)]['total_weight'] += vk.weight
        
        # 计算课程平均权重
        courses_data = []
        for course_info in course_map.values():
            course_info['avg_weight'] = round(
                course_info['total_weight'] / course_info['video_count'], 3
            ) if course_info['video_count'] > 0 else 0
            del course_info['total_weight']  # 移除临时字段
            courses_data.append(course_info)
        
        # 按视频数量排序
        courses_data.sort(key=lambda x: x['video_count'], reverse=True)
        
        return jsonify({
            'code': 200,
            'msg': '获取关键词使用情况成功',
            'data': {
                'keyword_info': {
                    'id': str(keyword.id),
                    'name': keyword.name,
                    'category': keyword.category,
                    'description': keyword.description
                },
                'usage_summary': {
                    'total_videos': len(videos_data),
                    'total_courses': len(courses_data),
                    'avg_weight': round(sum(vk.weight for vk, _, _ in video_usage) / len(video_usage), 3) if video_usage else 0
                },
                'videos': videos_data,
                'courses': courses_data
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/search', methods=['GET'])
@token_required  
def search_keywords():
    """搜索关键词"""
    try:
        # 获取查询参数
        query = request.args.get('q', '').strip()
        category = request.args.get('category')
        course_id = request.args.get('courseId')
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'code': 400,
                'msg': '搜索关键词不能为空',
                'data': None
            }), 400
        
        # 构建基础查询
        base_query = db.session.query(Keyword)
        
        # 添加搜索条件
        search_filter = db.or_(
            Keyword.name.contains(query),
            Keyword.description.contains(query)
        )
        base_query = base_query.filter(search_filter)
        
        # 添加分类过滤
        if category:
            base_query = base_query.filter(Keyword.category == category)
        
        # 添加课程过滤
        if course_id:
            base_query = base_query.join(CourseKeyword).filter(
                CourseKeyword.course_id == course_id
            )
        
        # 执行查询
        keywords = base_query.limit(limit).all()
        
        # 构建返回数据
        results = []
        for keyword in keywords:
            # 获取使用统计
            video_count = VideoKeyword.query.filter_by(keyword_id=keyword.id).count()
            course_count = CourseKeyword.query.filter_by(keyword_id=keyword.id).count()
            
            results.append({
                'id': str(keyword.id),
                'name': keyword.name,
                'category': keyword.category,
                'description': keyword.description,
                'usage_stats': {
                    'video_count': video_count,
                    'course_count': course_count
                }
            })
        
        return jsonify({
            'code': 200,
            'msg': '搜索关键词成功',
            'data': {
                'query': query,
                'results': results,
                'total_count': len(results)
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500

@knowledge_graph_bp.route('/api/knowledge-graph/course/<course_id>/videos-status', methods=['GET'])
@token_required
def get_course_videos_processing_status(course_id):
    """获取课程视频的知识图谱处理状态"""
    try:
        # 验证课程是否存在
        course = Course.query.get(course_id)
        if not course:
            return jsonify({
                'code': 404,
                'msg': '课程不存在',
                'data': None
            }), 404
        
        # 使用知识图谱处理器检查状态
        from tasks.knowledge_graph_processor import KnowledgeGraphProcessor
        processor = KnowledgeGraphProcessor()
        status = processor.check_videos_processed_status(course_id)
        
        return jsonify({
            'code': 200,
            'msg': '获取视频处理状态成功',
            'data': {
                'course_info': {
                    'id': str(course.id),
                    'name': course.name
                },
                'processing_status': status,
                'is_up_to_date': status['unprocessed_count'] == 0,
                'can_use_incremental': status['processed_count'] > 0 and status['unprocessed_count'] > 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'msg': f'服务器错误: {str(e)}',
            'data': None
        }), 500
