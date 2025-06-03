import os
from flask import Blueprint, request, jsonify, session
from models.models import Course, db, Users, Video, Document
from schemas.course_dto import CourseCreateDTO, CourseEditDTO
from schemas.course_vo import CourseVO, CourseDetailVO, TeacherInfoVO
from utils.result import Result
from datetime import datetime
from sqlalchemy import func
from utils.auth import token_required, get_current_user_id as jwt_get_user_id

course_bp = Blueprint('course', __name__)

def get_current_user_id():
    """获取当前登录用户ID"""
    return jwt_get_user_id()

def is_teacher_or_admin(user_id):
    """检查用户是否为教师或管理员"""
    if not user_id:
        return False
    
    user = Users.query.get(user_id)
    if not user:
        return False
        
    return user.role in ['teacher', 'admin']

@course_bp.route('/add', methods=['POST'])
@token_required
def add_course():
    """
    添加课程接口，需要教师或管理员权限
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取请求 JSON 数据
        data = request.get_json()
        
        # 处理公开课程字段
        if 'isPublic' in data:
            data['is_public'] = data['isPublic']
            
        dto = CourseCreateDTO(**data)
        
        # 从时间戳转换为时间戳整数值 (不再需要转换为日期对象)
        from datetime import datetime
        
        # 前端传来的时间戳是毫秒级的，直接存储即可
        start_date = dto.startDate if dto.startDate else None
        end_date = dto.endDate if dto.endDate else None
        
        # 创建课程对象
        course = Course(
            name=dto.name,
            code=dto.code,
            description=dto.description,
            image_url=dto.imageUrl,
            start_date=start_date,  # 直接存储时间戳
            end_date=end_date,      # 直接存储时间戳
            hours=dto.hours,
            status=dto.status,     # 现在是整数
            is_public=dto.is_public,  # 添加是否为公开课
            semester=dto.semester,
            teacher_id=user_id,  # 设置当前用户为课程教师
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        
        # 保存到数据库
        db.session.add(course)
        db.session.commit()

        
        
        # 刷新获取最新数据
        db.session.refresh(course)
        
        # 手动构建VO对象，处理整数时间戳
        course_vo = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description or "",
            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
            "startDate": course.start_date if course.start_date else 0,
            "endDate": course.end_date if course.end_date else 0,
            "hours": course.hours,
            "studentCount": course.student_count,
            "status": course.status,  # 已经是整数
            "isPublic": course.is_public,  # 添加是否为公开课
            "semester": course.semester,
            "createTime": course.create_time,
            "updateTime": course.update_time
        }
        
        return jsonify(Result.success(course_vo, "课程添加成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        return jsonify(Result.error(400, f"添加失败: {str(e)}"))

@course_bp.route('/edit/<course_id>', methods=['PUT'])
@token_required
def edit_course(course_id):
    """
    编辑课程接口，需要教师或管理员权限
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找课程
        course = Course.query.get(course_id)
        
        # 检查课程是否存在
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查课程是否已删除
        if course.is_deleted:
            return jsonify(Result.error(400, "课程已被删除"))
        
        # 检查是否为课程所有者或管理员
        if str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
            print(f"课程教师ID: {course.teacher_id}, 当前用户ID: {user_id}, 类型: {type(course.teacher_id)}, {type(user_id)}")
            return jsonify(Result.error(403, "无权修改他人创建的课程"))
        
        # 获取请求 JSON 数据
        data = request.get_json()
        # 处理公开课程字段
        if 'isPublic' in data:
            data['is_public'] = data['isPublic']
        
        # 输出接收到的数据用于调试
        print(f"接收到的数据: {data}")
        
        try:
            # 使用 DTO 验证和处理数据
            dto = CourseEditDTO(**data)
            
            # 更新课程信息
            course.name = dto.name
            course.description = dto.description
            course.image_url = dto.imageUrl
            
            # 直接使用时间戳，不再转换为日期对象
            course.start_date = dto.startDate if dto.startDate else None
            course.end_date = dto.endDate if dto.endDate else None
            
            course.hours = dto.hours
            course.status = dto.status  # 现在是整数类型
            course.is_public = dto.is_public  # 更新是否为公开课
            course.semester = dto.semester
            course.update_time = datetime.now()
            
            # 提交更改
            db.session.commit()
            
            # 刷新获取最新数据
            db.session.refresh(course)
            
        except Exception as validation_error:
            print(f"验证错误: {validation_error}")
            return jsonify(Result.error(400, f"数据验证失败: {str(validation_error)}"))
        
        # 手动构建VO对象，将日期对象转换为时间戳
        course_vo = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description or "",
            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
            "startDate": course.start_date if course.start_date else 0,  # 已经是时间戳，直接使用
            "endDate": course.end_date if course.end_date else 0,  # 已经是时间戳，直接使用
            "hours": course.hours,
            "studentCount": course.student_count,
            "status": course.status,
            "isPublic": course.is_public,
            "semester": course.semester,
            "createTime": course.create_time,
            "updateTime": course.update_time
        }
        
        return jsonify(Result.success(course_vo, "课程更新成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        print(f"更新失败: {str(e)}")
        return jsonify(Result.error(400, f"更新失败: {str(e)}"))

@course_bp.route('/delete/<course_id>', methods=['DELETE'])
@token_required
def delete_course(course_id):
    """
    删除课程接口，需要教师或管理员权限
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 查找课程
        course = Course.query.get(course_id)
        
        # 检查课程是否存在
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查是否为课程所有者或管理员
        if str(course.teacher_id) != str(user_id) and not Users.query.get(user_id).role == 'admin':
            print(f"删除操作 - 课程教师ID: {course.teacher_id}, 当前用户ID: {user_id}, 类型: {type(course.teacher_id)}, {type(user_id)}")
            return jsonify(Result.error(403, "无权删除他人创建的课程"))
        
        # 标记为已删除
        course.is_deleted = True
        course.update_time = datetime.now()
        
        # 提交更改
        db.session.commit()
        
        return jsonify(Result.success(None, "课程删除成功"))
        
    except Exception as e:
        # 如果有错误，回滚事务
        db.session.rollback()
        return jsonify(Result.error(400, f"删除失败: {str(e)}"))

@course_bp.route('/list', methods=['GET'])
@token_required
def list_courses():
    """
    获取课程列表接口，需要教师或管理员权限
    """
    try:
        # 检查权限 (使用JWT中的用户ID)
        user_id = request.user.get('user_id')
        if not is_teacher_or_admin(user_id):
            return jsonify(Result.error(403, "无权操作，需要教师或管理员权限"))
            
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        size = request.args.get('size', 10, type=int)
        
        # 构建查询
        query = Course.query.filter_by(is_deleted=False)
        
        # 如果不是管理员，只能查看自己创建的课程
        user = Users.query.get(user_id)
        if user.role != 'admin':
            query = query.filter_by(teacher_id=user_id)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        courses = query.order_by(Course.create_time.desc()).offset((page - 1) * size).limit(size).all()
        
        # 手动构建VO列表
        course_list = []
        for course in courses:
            course_list.append({
                "id": course.id,
                "name": course.name,
                "code": course.code,
                "description": course.description or "",
                "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
                "startDate": course.start_date if course.start_date else 0,
                "endDate": course.end_date if course.end_date else 0,
                "hours": course.hours,
                "studentCount": course.student_count,
                "status": course.status,  # 已经是整数类型
                "isPublic": course.is_public,  # 添加是否为公开课
                "semester": course.semester,
                "createTime": course.create_time,
                "updateTime": course.update_time
            })
        
        return jsonify(Result.success({
            "total": total,
            "list": course_list,
            "page": page,
            "size": size
        }, "获取课程列表成功"))
        
    except Exception as e:
        return jsonify(Result.error(400, f"获取课程列表失败: {str(e)}"))

@course_bp.route('/detail/<course_id>', methods=['GET'])
def get_course_detail(course_id):
    """
    获取课程详情接口
    """
    try:
        # 查找课程
        course = Course.query.get(course_id)
        
        # 检查课程是否存在
        if not course:
            return jsonify(Result.error(404, "课程不存在"))
        
        # 检查课程是否已删除
        if course.is_deleted:
            return jsonify(Result.error(400, "课程已被删除"))
        
        # 使用ORM关系获取教师信息
        teacher_info = {"id": 0, "name": "未分配"}
        if course.teacher:
            teacher_info = {"id": course.teacher.id, "name": course.teacher.username}
        
        # 使用ORM关系获取视频数量
        video_count = course.videos.filter_by(is_deleted=False).count()
          # 使用ORM关系获取课件数量
        material_count = course.documents.filter_by(is_deleted=False).count()
        
        # 获取该课程下的所有未删除视频，按视频标题字典序排序
        videos = course.videos.filter_by(is_deleted=False).order_by(Video.title.asc()).all()
        
        # 构建视频列表
        video_list = []
        for video in videos:
            video_list.append({
                "id": video.id,
                "title": video.title,
                "description": video.description or "",
                "coverUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{video.cover_url}" or video.cover_url,
                "duration": video.duration,
                "uploadTime": video.upload_time.isoformat(),
                "viewCount": video.view_count,
                "commentCount": video.comment_count
            })
        
        # 手动构建详细VO对象
        course_detail = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
            "description": course.description or "",
            "imageUrl": os.getenv('IS_DEBUG') == 'True' and f"http://localhost:5000{course.image_url}" or course.image_url or "",
            "startDate": course.start_date if course.start_date else 0,
            "endDate": course.end_date if course.end_date else 0,
            "hours": course.hours,
            "studentCount": course.student_count,
            "status": course.status,  # 已经是整数类型
            "isPublic": course.is_public,  # 添加是否为公开课
            "semester": course.semester,
            "createTime": course.create_time,
            "updateTime": course.update_time,
            "teacherInfo": teacher_info,
            "videoCount": video_count,
            "materialCount": material_count,
            "videos": video_list  # 添加视频列表到返回数据中
        }
        
        return jsonify(Result.success(course_detail, "获取课程详情成功"))
        
    except Exception as e:
        return jsonify(Result.error(400, f"获取课程详情失败: {str(e)}"))