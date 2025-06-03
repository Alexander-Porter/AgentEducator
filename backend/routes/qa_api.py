"""重构后的QA API路由模块 - 只处理HTTP请求和响应"""
import time
import traceback
from flask import Blueprint, request, jsonify, current_app, Response, stream_with_context
from utils.auth import token_required
from utils.result import Result
from models.models import Course, db
from services.chat_service import chat_service
from services.index_service import index_service
from services.course_access_service import course_access_service
from services.streaming_service import streaming_service
from services.cache_service import get_video_info

qa_bp = Blueprint('qa', __name__)


@qa_bp.route('/ask-stream', methods=['POST'])
@token_required
def ask_question_stream():
    """处理流式问答请求（重构版）"""
    try:
        start_time = time.time()
        
        # 解析请求参数
        request_data = _parse_request_data()
        if isinstance(request_data, tuple):  # 错误响应
            return request_data[0]
        
        # 检查模式类型
        if request_data['is_general_llm']:
            return _handle_general_llm_mode(request_data, start_time)
        else:
            return _handle_rag_mode(request_data, start_time)
        
    except Exception as e:
        current_app.logger.error(f"处理请求失败: {str(e)}")
        print(traceback.format_exc())
        db.session.rollback()
        return jsonify(Result.error(500, f"处理请求失败: {str(e)}"))


def _parse_request_data():
    """解析请求数据"""
    data = request.get_json()
    if not data:
        return jsonify(Result.error(400, "缺少请求数据")), None
        
    query = data.get('query')
    if not query:
        return jsonify(Result.error(400, "问题不能为空")), None
    
    video_id = data.get('videoId')
    course_id = data.get('courseId')
    session_id = data.get('sessionId')
    ask_course = data.get('askCourse', False)
    ask_all_course = data.get('askAllCourse', False)
    is_new_session = data.get('isNewSession', False)
    history = data.get('history', [])
    user_id = request.user.get('user_id')
    
    # 检查是否为通用LLM模式
    is_general_llm = not (video_id or course_id or ask_course or ask_all_course)
    
    return {
        'query': query,
        'video_id': video_id,
        'course_id': course_id,
        'session_id': session_id,
        'ask_course': ask_course,
        'ask_all_course': ask_all_course,
        'is_new_session': is_new_session,
        'history': history,
        'user_id': user_id,
        'is_general_llm': is_general_llm
    }


def _handle_general_llm_mode(request_data, start_time):
    """处理通用LLM模式"""
    # 创建或获取会话
    title = f"通用问答 - {request_data['query'][:20]}{'...' if len(request_data['query']) > 20 else ''}"
    session_id = chat_service.create_or_get_session(
        request_data['session_id'],
        request_data['user_id'],
        title,
        is_new_session=request_data['is_new_session']
    )
    
    # 保存用户问题
    chat_service.save_message_to_db(session_id, 'user', request_data['query'])
    
    # 创建流式生成器
    generate = streaming_service.create_general_stream_generator(
        request_data['query'],
        session_id,
        request_data['history']
    )
    
    # 返回流式响应
    resp = Response(
        stream_with_context(generate()),
        content_type='text/event-stream'
    )
    resp.headers['X-Session-Id'] = str(session_id)
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Connection'] = 'keep-alive'
    
    return resp


def _handle_rag_mode(request_data, start_time):
    """处理RAG模式"""
    # 处理不同的RAG模式
    rag_result = _process_rag_mode(request_data)
    if isinstance(rag_result, tuple) and len(rag_result) == 2 and rag_result[1] is None:
        return rag_result[0]  # 错误响应
    
    session_id, index, error = rag_result
    
    if error:
        return jsonify(Result.error(500, error))
    
    # 创建流式生成器
    generate = streaming_service.create_rag_stream_generator(
        request_data['query'],
        session_id,
        request_data['history'],
        request_data['video_id'],
        request_data['course_id'],
        index
    )
    
    # 返回流式响应
    resp = Response(
        stream_with_context(generate()),
        content_type='text/event-stream'
    )
    resp.headers['X-Session-Id'] = str(session_id)
    resp.headers['Cache-Control'] = 'no-cache'
    resp.headers['Connection'] = 'keep-alive'
    
    total_time = time.time() - start_time
    current_app.logger.info(f"请求处理完成，总耗时: {total_time:.2f}s")
    
    return resp


def _process_rag_mode(request_data):
    """处理RAG模式的不同情况"""
    if request_data['ask_all_course']:
        return _handle_all_course_mode(request_data)
    elif request_data['ask_course'] and request_data['course_id']:
        return _handle_single_course_mode(request_data)
    elif request_data['video_id']:
        return _handle_video_mode(request_data)
    else:
        return jsonify(Result.error(400, "视频ID或课程ID不能为空")), None


def _handle_all_course_mode(request_data):
    """处理跨课程问答模式"""
    # 获取用户可访问的课程
    accessible_course_ids = course_access_service.get_accessible_course_ids(request_data['user_id'])
    
    if not accessible_course_ids:
        return jsonify(Result.error(400, "没有找到可用的课程")), None
    
    # 创建会话
    title = f"跨课程问答 - {request_data['query'][:20]}{'...' if len(request_data['query']) > 20 else ''}"
    session_id = chat_service.create_or_get_session(
        request_data['session_id'],
        request_data['user_id'],
        title,
        is_new_session=request_data['is_new_session']
    )
    
    # 保存用户问题
    chat_service.save_message_to_db(session_id, 'user', request_data['query'])
    
    # 获取合并索引
    index, error = index_service.merge_course_indices(accessible_course_ids)
    
    return session_id, index, error


def _handle_single_course_mode(request_data):
    """处理单课程问答模式"""
    course_id = request_data['course_id']
    
    # 创建会话
    course = Course.query.get(course_id)
    title = f"关于 {course.name if course else '未知课程'} 的提问"
    session_id = chat_service.create_or_get_session(
        request_data['session_id'],
        request_data['user_id'],
        title,
        course_id=course_id,
        is_new_session=request_data['is_new_session']
    )
    
    # 保存用户问题
    chat_service.save_message_to_db(session_id, 'user', request_data['query'])
    
    # 获取课程索引
    index, error = index_service.get_course_video_index(course_id)
    
    return session_id, index, error


def _handle_video_mode(request_data):
    """处理视频问答模式"""
    video_id = request_data['video_id']
    course_id = request_data['course_id']
    
    # 创建会话
    video_title, _ = get_video_info(video_id)
    title = f"关于 {video_title if video_title else '未知视频'} 的提问"
    session_id = chat_service.create_or_get_session(
        request_data['session_id'],
        request_data['user_id'],
        title,
        video_id=video_id,
        course_id=course_id,
        is_new_session=request_data['is_new_session']
    )
    
    # 保存用户问题
    chat_service.save_message_to_db(session_id, 'user', request_data['query'])
    
    # 获取视频索引
    index, error = index_service.get_video_index(video_id)
    
    return session_id, index, error
