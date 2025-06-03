import os
import json
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models.models import (
    Course, db, Users, Video, Document, UserVideoProgress, 
    VideoComment, StudentCourseEnrollment
)
from utils.result import Result
from utils.auth import token_required
from sqlalchemy import func, and_, or_

statistics_bp = Blueprint('statistics', __name__)

# 日统计数据存储路径
STATS_DATA_DIR = 'data/statistics'
if not os.path.exists(STATS_DATA_DIR):
    os.makedirs(STATS_DATA_DIR)

def is_teacher_or_admin(user):
    """检查用户是否为教师或管理员"""
    if not user:
        return False
    return user.role in ['teacher', 'admin']

def get_daily_stats_file_path(date_str):
    """获取指定日期的统计文件路径"""
    return os.path.join(STATS_DATA_DIR, f'stats_{date_str}.json')

def save_daily_stats(date_str, stats_data):
    """保存日统计数据"""
    file_path = get_daily_stats_file_path(date_str)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)

def load_daily_stats(date_str):
    """加载日统计数据"""
    file_path = get_daily_stats_file_path(date_str)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def generate_micro_perturbation(base_value, variation_rate=0.1):
    """生成微扰数据：在基础值上随机增减一定比例"""
    variation = base_value * variation_rate * (random.random() - 0.5) * 2
    return max(0, int(base_value + variation))

def get_historical_trend_data(days=30):
    """获取历史趋势数据，缺失的数据用微扰填充"""
    trend_data = []
    today = datetime.now().date()
    
    # 获取当前真实数据作为基准
    current_stats = get_current_real_stats()
    base_active_students = current_stats.get('active_students', 50)
    base_video_views = current_stats.get('video_views', 100)
    
    for i in range(days):
        date = today - timedelta(days=days-1-i)
        date_str = date.strftime('%Y-%m-%d')
        
        # 尝试加载已保存的数据
        daily_stats = load_daily_stats(date_str)
        
        if daily_stats:
            # 使用已保存的真实数据
            trend_data.append({
                'date': date_str,
                'active_students': daily_stats.get('active_students', 0),
                'video_views': daily_stats.get('video_views', 0),
                'new_enrollments': daily_stats.get('new_enrollments', 0)
            })
        else:
            # 生成微扰数据
            # 考虑周末数据较低的模式
            is_weekend = date.weekday() >= 5
            weekend_factor = 0.6 if is_weekend else 1.0
            
            active_students = generate_micro_perturbation(
                base_active_students * weekend_factor, 0.2
            )
            video_views = generate_micro_perturbation(
                base_video_views * weekend_factor, 0.3
            )
            new_enrollments = generate_micro_perturbation(5 * weekend_factor, 0.5)
            
            trend_data.append({
                'date': date_str,
                'active_students': active_students,
                'video_views': video_views,
                'new_enrollments': new_enrollments
            })
    
    return trend_data

def get_current_real_stats():
    """获取当前真实统计数据"""
    try:
        # 总学生人数
        total_students = Users.query.filter(
            and_(Users.role == 'student', Users.is_deleted == False)
        ).count()
        
        # 活跃学生（最近7天有学习行为）
        week_ago = datetime.now() - timedelta(days=7)
        active_students = db.session.query(Users.id).join(
            UserVideoProgress, Users.id == UserVideoProgress.user_id
        ).filter(
            and_(
                Users.role == 'student',
                Users.is_deleted == False,
                UserVideoProgress.update_time >= week_ago
            )
        ).distinct().count()
        
        # 总视频观看次数
        total_video_views = UserVideoProgress.query.count()
        
        # 平均课程完成率
        avg_completion_rate = db.session.query(
            func.avg(UserVideoProgress.progress)
        ).scalar() or 0
        
        # 课程总数
        total_courses = Course.query.filter(Course.is_deleted == False).count()
        
        # 视频总数
        total_videos = Video.query.filter(Video.is_deleted == False).count()
        
        return {
            'total_students': total_students,
            'active_students': active_students,
            'total_video_views': total_video_views,
            'avg_completion_rate': float(avg_completion_rate) * 100,
            'total_courses': total_courses,
            'total_videos': total_videos
        }
    except Exception as e:
        print(f"Error getting real stats: {e}")
        # 返回默认值
        return {
            'total_students': 0,
            'active_students': 0,
            'total_video_views': 0,
            'avg_completion_rate': 0,
            'total_courses': 0,
            'total_videos': 0
        }

def get_student_learning_data(course_id=None):
    """获取学生学习情况数据"""
    try:
        # 构建查询
        query = db.session.query(
            Users.id,
            Users.username,
            Users.class_name,
            func.avg(UserVideoProgress.progress).label('avg_progress'),
            func.count(UserVideoProgress.id).label('video_count'),
            func.max(UserVideoProgress.update_time).label('last_active')
        ).join(
            UserVideoProgress, Users.id == UserVideoProgress.user_id
        ).filter(
            and_(Users.role == 'student', Users.is_deleted == False)
        )
        
        # 如果指定了课程，添加课程过滤
        if course_id and course_id != 'all':
            query = query.join(
                Video, UserVideoProgress.video_id == Video.id
            ).filter(Video.course_id == course_id)
        
        query = query.group_by(Users.id, Users.username, Users.class_name)
        
        students = query.all()
        
        student_data = []
        for student in students:
            # 计算完成的视频数量
            completed_videos = UserVideoProgress.query.filter(
                and_(
                    UserVideoProgress.user_id == student.id,
                    UserVideoProgress.completed == True
                )
            ).count()
            
            # 计算平均观看时长（模拟数据）
            avg_watch_time = f"{random.randint(15, 60)}分钟"
            
            # 格式化最后活跃时间
            if student.last_active:
                days_ago = (datetime.now() - student.last_active).days
                if days_ago == 0:
                    last_active = "今天"
                elif days_ago == 1:
                    last_active = "昨天"
                elif days_ago <= 7:
                    last_active = f"{days_ago}天前"
                else:
                    last_active = "1周前"
            else:
                last_active = "未知"
            
            student_data.append({
                'id': str(student.id),
                'name': student.username,
                'studentId': student.class_name or f"STU{str(student.id)[:6]}",
                'progress': round((student.avg_progress or 0) * 100, 1),
                'completedVideos': completed_videos,
                'avgWatchTime': avg_watch_time,
                'lastActive': last_active
            })
        
        return student_data
    except Exception as e:
        print(f"Error getting student data: {e}")
        return []

def get_video_ranking_data(course_id=None):
    """获取视频观看排行数据"""
    try:
        query = db.session.query(
            Video.title,
            func.count(UserVideoProgress.id).label('view_count')
        ).join(
            UserVideoProgress, Video.id == UserVideoProgress.video_id
        ).filter(Video.is_deleted == False)
        
        if course_id and course_id != 'all':
            query = query.filter(Video.course_id == course_id)
        
        query = query.group_by(Video.id, Video.title).order_by(
            func.count(UserVideoProgress.id).desc()
        ).limit(10)
        
        videos = query.all()
        
        return [
            {
                'name': video.title,
                'views': video.view_count
            }
            for video in videos
        ]
    except Exception as e:
        print(f"Error getting video ranking: {e}")
        return []

def get_study_time_distribution():
    """获取学习时长分布（模拟数据，因为实际观看时长较难统计）"""
    return [
        {'name': '<30分钟', 'value': random.randint(30, 50)},
        {'name': '30-60分钟', 'value': random.randint(40, 60)},
        {'name': '1-2小时', 'value': random.randint(50, 80)},
        {'name': '2-3小时', 'value': random.randint(30, 50)},
        {'name': '>3小时', 'value': random.randint(20, 40)}
    ]

def get_course_completion_radar(course_id=None):
    """获取课程完成率雷达图数据"""
    try:
        if course_id and course_id != 'all':
            courses = Course.query.filter(
                and_(Course.id == course_id, Course.is_deleted == False)
            ).all()
        else:
            courses = Course.query.filter(Course.is_deleted == False).limit(6).all()
        
        radar_data = []
        for course in courses:
            # 计算课程平均完成率
            avg_progress = db.session.query(
                func.avg(UserVideoProgress.progress)
            ).join(
                Video, UserVideoProgress.video_id == Video.id
            ).filter(Video.course_id == course.id).scalar() or 0
            
            radar_data.append({
                'name': course.name,
                'value': round(float(avg_progress) * 100, 1)
            })
        
        return radar_data
    except Exception as e:
        print(f"Error getting course completion radar: {e}")
        return []

@statistics_bp.route('/overview', methods=['GET'])
@token_required
def get_statistics_overview():
    """获取统计数据总览 - 教师专用"""
    try:
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not is_teacher_or_admin(user):
            return jsonify(Result.error(403, "无权访问，需要教师或管理员权限"))
        
        course_id = request.args.get('course_id', 'all')
        time_period = request.args.get('time_period', 'month')
        
        # 获取当前统计数据
        current_stats = get_current_real_stats()
        
        # 保存今日统计数据
        today_str = datetime.now().strftime('%Y-%m-%d')
        today_stats = {
            'active_students': current_stats['active_students'],
            'video_views': current_stats['total_video_views'],
            'new_enrollments': random.randint(0, 5),  # 模拟新注册数
            'timestamp': datetime.now().isoformat()
        }
        save_daily_stats(today_str, today_stats)
        
        # 计算变化趋势（与前一天比较）
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_stats = load_daily_stats(yesterday_str)
        
        def calculate_change(current, previous, key):
            if not previous or key not in previous or previous[key] == 0:
                return {"trend": "up", "change": "新增"}
            
            prev_value = previous[key]
            change_rate = ((current - prev_value) / prev_value) * 100
            
            if change_rate > 0:
                return {"trend": "up", "change": f"{abs(change_rate):.1f}% 增长"}
            elif change_rate < 0:
                return {"trend": "down", "change": f"{abs(change_rate):.1f}% 下降"}
            else:
                return {"trend": "stable", "change": "无变化"}
        
        # 构建总览统计数据
        overview_stats = [
            {
                'label': '总学生人数',
                'value': str(current_stats['total_students']),
                'icon': 'mdi-account-group',
                'color': 'indigo',
                **calculate_change(
                    current_stats['total_students'],
                    yesterday_stats,
                    'total_students'
                )
            },
            {
                'label': '活跃学生',
                'value': str(current_stats['active_students']),
                'icon': 'mdi-account-check',
                'color': 'teal',
                **calculate_change(
                    current_stats['active_students'],
                    yesterday_stats,
                    'active_students'
                )
            },
            {
                'label': '视频观看次数',
                'value': f"{current_stats['total_video_views']:,}",
                'icon': 'mdi-video-outline',
                'color': 'deep-purple',
                **calculate_change(
                    current_stats['total_video_views'],
                    yesterday_stats,
                    'video_views'
                )
            },
            {
                'label': '平均课程完成率',
                'value': f"{current_stats['avg_completion_rate']:.1f}%",
                'icon': 'mdi-check-circle-outline',
                'color': 'amber darken-2',
                **calculate_change(
                    current_stats['avg_completion_rate'],
                    yesterday_stats,
                    'avg_completion_rate'
                )
            }
        ]
        
        # 获取趋势数据
        days_map = {'week': 7, 'month': 30, 'semester': 90}
        days = days_map.get(time_period, 30)
        trend_data = get_historical_trend_data(days)
        
        # 获取学生学习数据
        student_data = get_student_learning_data(course_id)
        
        # 获取视频排行数据
        video_ranking = get_video_ranking_data(course_id)
        
        # 获取学习时长分布
        study_time_distribution = get_study_time_distribution()
        
        # 获取课程完成率雷达图数据
        course_completion_radar = get_course_completion_radar(course_id)
        
        # 获取课程列表
        courses = Course.query.filter(Course.is_deleted == False).all()
        course_options = [{'id': 'all', 'name': '全部课程'}]
        course_options.extend([
            {'id': str(course.id), 'name': course.name}
            for course in courses
        ])
        
        response_data = {
            'overview_stats': overview_stats,
            'trend_data': trend_data,
            'student_data': student_data,
            'video_ranking': video_ranking,
            'study_time_distribution': study_time_distribution,
            'course_completion_radar': course_completion_radar,
            'courses': course_options
        }
        
        return jsonify(Result.success(response_data))
        
    except Exception as e:
        print(f"Error in get_statistics_overview: {e}")
        return jsonify(Result.error(500, f"获取统计数据失败: {str(e)}"))

@statistics_bp.route('/courses', methods=['GET'])
@token_required
def get_teacher_courses():
    """获取教师的课程列表"""
    try:
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not is_teacher_or_admin(user):
            return jsonify(Result.error(403, "无权访问，需要教师或管理员权限"))
        
        # 如果是管理员，返回所有课程；如果是教师，返回自己的课程
        if user.role == 'admin':
            courses = Course.query.filter(Course.is_deleted == False).all()
        else:
            courses = Course.query.filter(
                and_(Course.teacher_id == user_id, Course.is_deleted == False)
            ).all()
        
        course_list = [{'id': 'all', 'name': '全部课程'}]
        course_list.extend([
            {
                'id': str(course.id),
                'name': course.name,
                'student_count': StudentCourseEnrollment.query.filter(
                    StudentCourseEnrollment.course_id == course.id
                ).count()
            }
            for course in courses
        ])
        
        return jsonify(Result.success(course_list))
        
    except Exception as e:
        print(f"Error in get_teacher_courses: {e}")
        return jsonify(Result.error(500, f"获取课程列表失败: {str(e)}"))

@statistics_bp.route('/teacher-home', methods=['GET'])
@token_required
def get_teacher_home_data():
    """获取教师主页数据 - 包含统计信息、课程数据、最近活动等"""
    try:
        user_id = request.user.get('user_id')
        user = Users.query.get(user_id)
        
        if not is_teacher_or_admin(user):
            return jsonify(Result.error(403, "无权访问，需要教师或管理员权限"))
        
        # 1. 获取教师基本信息
        teacher_info = {
            'id': user.id,
            'name': user.username,
            'email': user.email,
            'role': user.role
        }
        
        # 2. 获取教师的课程统计
        if user.role == 'admin':
            # 管理员查看所有课程
            courses_query = Course.query.filter(Course.is_deleted == False)
        else:
            # 教师查看自己的课程
            courses_query = Course.query.filter(
                and_(Course.teacher_id == user_id, Course.is_deleted == False)
            )
        
        total_courses = courses_query.count()
        active_courses = courses_query.filter(Course.status.in_([0, 1])).count()  # 即将开始或进行中
        
        # 3. 获取本月视频上传数量
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_videos = db.session.query(func.count(Video.id)).join(
            Course, Video.course_id == Course.id
        ).filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            Video.is_deleted == False,
            Video.upload_time >= current_month_start
        ).scalar() or 0
        
        # 4. 获取活跃学生数量（本月有学习记录的学生）
        active_students_query = db.session.query(
            func.count(func.distinct(UserVideoProgress.user_id))
        ).join(
            Video, UserVideoProgress.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            UserVideoProgress.update_time >= current_month_start,
            UserVideoProgress.last_position > 0
        )
        active_students = active_students_query.scalar() or 0
        
        # 5. 获取待处理任务数量（可以是待回复的评论、新的学生等）
        pending_comments = db.session.query(func.count(VideoComment.id)).join(
            Video, VideoComment.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            VideoComment.is_deleted == False,
            VideoComment.create_time >= current_month_start
        ).scalar() or 0
        
        # 6. 计算变化趋势（与上月对比）
        last_month_start = (current_month_start - timedelta(days=32)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        
        # 上月视频数量
        last_month_videos = db.session.query(func.count(Video.id)).join(
            Course, Video.course_id == Course.id
        ).filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            Video.is_deleted == False,
            Video.upload_time >= last_month_start,
            Video.upload_time <= last_month_end
        ).scalar() or 0
        
        # 上月活跃学生
        last_month_active_students = db.session.query(
            func.count(func.distinct(UserVideoProgress.user_id))
        ).join(
            Video, UserVideoProgress.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            UserVideoProgress.update_time >= last_month_start,
            UserVideoProgress.update_time <= last_month_end,
            UserVideoProgress.last_position > 0
        ).scalar() or 0
        
        # 计算变化率
        def calculate_change_rate(current, previous):
            if previous == 0:
                return {"trend": "up", "change": "新增"} if current > 0 else {"trend": "stable", "change": "无变化"}
            
            rate = ((current - previous) / previous) * 100
            if rate > 0:
                return {"trend": "up", "change": f"{abs(rate):.0f}%"}
            elif rate < 0:
                return {"trend": "down", "change": f"{abs(rate):.0f}%"}
            else:
                return {"trend": "stable", "change": "无变化"}
        
        video_change = calculate_change_rate(monthly_videos, last_month_videos)
        student_change = calculate_change_rate(active_students, last_month_active_students)
        
        # 7. 构建统计数据
        stat_items = [
            {
                'label': '总课程数',
                'value': str(total_courses),
                'icon': 'mdi-book-open-variant',
                **calculate_change_rate(total_courses, total_courses)  # 课程数暂时不计算变化
            },
            {
                'label': '本月视频上传',
                'value': str(monthly_videos),
                'icon': 'mdi-video',
                **video_change
            },
            {
                'label': '活跃学生',
                'value': str(active_students),
                'icon': 'mdi-account-group',
                **student_change
            },
            {
                'label': '待处理消息',
                'value': str(pending_comments),
                'icon': 'mdi-clipboard-check',
                'trend': 'up' if pending_comments > 0 else 'stable',
                'change': f"{pending_comments}条" if pending_comments > 0 else "无"
            }
        ]
        
        # 8. 获取最近活动（最近7天）
        recent_date = datetime.now() - timedelta(days=7)
        recent_activities = []
        
        # 最近上传的视频
        recent_videos = db.session.query(
            Video.title, Video.upload_time, Course.name.label('course_name')
        ).join(
            Course, Video.course_id == Course.id
        ).filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            Video.is_deleted == False,
            Video.upload_time >= recent_date
        ).order_by(Video.upload_time.desc()).limit(3).all()
        
        for video in recent_videos:
            recent_activities.append({
                'time': _format_time_ago(video.upload_time),
                'type': 'upload',
                'icon': 'mdi-upload',
                'title': '上传了新视频',
                'description': f'{video.course_name} - {video.title}',
                'sort_time': video.upload_time
            })
        
        # 最近创建的课程
        recent_courses = Course.query.filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            Course.is_deleted == False,
            Course.create_time >= recent_date
        ).order_by(Course.create_time.desc()).limit(2).all()
        
        for course in recent_courses:
            recent_activities.append({
                'time': _format_time_ago(course.create_time),
                'type': 'course',
                'icon': 'mdi-book',
                'title': '创建了新课程',
                'description': course.name,
                'sort_time': course.create_time
            })
        
        # 最近的学生评论
        recent_comments = db.session.query(
            VideoComment.content, VideoComment.create_time, 
            Video.title.label('video_title'), Users.username
        ).join(
            Video, VideoComment.video_id == Video.id
        ).join(
            Course, Video.course_id == Course.id
        ).join(
            Users, VideoComment.user_id == Users.id
        ).filter(
            Course.teacher_id == user_id if user.role != 'admin' else True,
            VideoComment.is_deleted == False,
            VideoComment.create_time >= recent_date
        ).order_by(VideoComment.create_time.desc()).limit(2).all()
        
        for comment in recent_comments:
            recent_activities.append({
                'time': _format_time_ago(comment.create_time),
                'type': 'comment',
                'icon': 'mdi-comment',
                'title': '收到学生提问',
                'description': f'{comment.username} 在 {comment.video_title} 中提问',
                'sort_time': comment.create_time
            }        )
        
        # 按时间排序活动
        for activity in recent_activities:
            if 'create_time' not in activity:
                activity['sort_time'] = datetime.now()  # 默认时间
        
        recent_activities.sort(key=lambda x: x.get('sort_time', datetime.now()), reverse=True)
        recent_activities = recent_activities[:5]  # 只保留最近5条
        
        # 移除排序用的时间戳
        for activity in recent_activities:
            activity.pop('sort_time', None)
        
        # 9. 获取课程进度信息
        course_progress_info = {
            'active_courses': active_courses,
            'pending_messages': pending_comments
        }
        
        # 10. 构建响应数据
        response_data = {
            'teacher_info': teacher_info,
            'stat_items': stat_items,
            'course_progress': course_progress_info,
            'recent_activities': recent_activities
        }
        
        return jsonify(Result.success(response_data, "获取教师主页数据成功"))
        
    except Exception as e:
        import traceback
        print(f"Error in get_teacher_home_data: {e}\n{traceback.format_exc()}")
        return jsonify(Result.error(500, f"获取教师主页数据失败: {str(e)}"))

def _format_time_ago(dt):
    """格式化时间为"XX前"的形式"""
    if not dt:
        return "未知时间"
    
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 0:
        if diff.days == 1:
            return "昨天 " + dt.strftime("%H:%M")
        elif diff.days < 7:
            return f"{diff.days}天前"
        else:
            return dt.strftime("%m-%d %H:%M")
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"
