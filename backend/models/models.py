from flask_sqlalchemy import SQLAlchemy
import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.types import TypeDecorator
from datetime import datetime
import json

db = SQLAlchemy()

# 创建自定义UUID类型转换器
class UUIDType(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)

    def is_mutable(self):
        return False

class Users(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # teacher, student
    avatar = db.Column(db.String(255))  # 用户头像URL
    class_name = db.Column(db.String(50))  # 学生所属班级
    status = db.Column(db.String(20), default='active')  # 学生状态: active, inactive, graduated
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 添加关系，使查询更方便 - 修改为使用back_populates
    taught_courses = db.relationship('Course', backref='teacher', lazy='dynamic', 
                                     foreign_keys='Course.teacher_id')
    enrolled_courses = db.relationship('StudentCourseEnrollment', backref='student', 
                                      lazy='dynamic', foreign_keys='StudentCourseEnrollment.student_id')
    permissions = db.relationship('UserPermission', back_populates='user')  # 使用back_populates
    video_progress = db.relationship('UserVideoProgress', backref='user', lazy='dynamic')
    comments = db.relationship('VideoComment', backref='user', lazy='dynamic')

class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    start_date = db.Column(db.BigInteger, nullable=False, comment='课程开始日期(时间戳)')
    end_date = db.Column(db.BigInteger, nullable=False, comment='课程结束日期(时间戳)')
    hours = db.Column(db.Integer, nullable=False)
    student_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, nullable=False, comment='课程状态: 0=upcoming, 1=active, 2=completed')  # 从字符串改为整数
    is_public = db.Column(db.Boolean, default=False, comment='是否为公开课')  # 新增字段：是否为公开课
    semester = db.Column(db.String(20), nullable=False)
    teacher_id = db.Column(UUIDType, db.ForeignKey('users.id'))  # 添加教师ID字段
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 添加关系，使查询更方便
    videos = db.relationship('Video', backref='course', lazy='dynamic')
    documents = db.relationship('Document', backref='course', lazy='dynamic')
    enrollments = db.relationship('StudentCourseEnrollment', backref='course', lazy='dynamic')

class Video(db.Model):
    """视频资源"""
    __tablename__ = 'videos'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4, comment='视频ID')
    title = db.Column(db.String(255), nullable=False, comment='视频标题')
    description = db.Column(db.Text, nullable=True, comment='视频描述')
    cover_url = db.Column(db.String(255), nullable=True, comment='封面图URL')
    video_url = db.Column(db.String(255), nullable=False, comment='视频URL')
    duration = db.Column(db.Integer, nullable=False, default=0, comment='视频时长(秒)')
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False, comment='所属课程ID')
    view_count = db.Column(db.Integer, default=0, comment='观看次数')
    comment_count = db.Column(db.Integer, default=0, comment='评论数量')
    upload_time = db.Column(db.DateTime, default=datetime.now, comment='上传时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否删除')
    completed_count = db.Column(db.Integer, default=0, comment='完成观看的人数')
    
    # 关系
    comments = db.relationship('VideoComment', backref='video', lazy='dynamic')
    progress_records = db.relationship('UserVideoProgress', backref='video', lazy='dynamic')
    summary = db.relationship('VideoSummary', backref='video', uselist=False)
    # 修改为使用back_populates代替backref
    processing_tasks = db.relationship('VideoProcessingTask', back_populates='video', lazy=True)
    
    @property
    def completion_rate(self):
        """计算视频完成率"""
        if self.view_count == 0:
            return 0
        return self.completed_count / self.view_count if self.view_count > 0 else 0

class VideoComment(db.Model):
    __tablename__ = 'video_comments'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    content = db.Column(db.Text, nullable=False)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(UUIDType, db.ForeignKey('video_comments.id'))  # 回复的评论ID
    time_point = db.Column(db.Integer)  # 视频时间点（秒）
    create_time = db.Column(db.DateTime, default=datetime.now)
    likes = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 添加回复关系，方便获取评论的回复
    replies = db.relationship('VideoComment', 
                             backref=db.backref('parent', remote_side=[id]),
                             lazy='dynamic')
    
    # 添加点赞关系
    liked_by = db.relationship('CommentLike', backref='comment', lazy='dynamic')

class CommentLike(db.Model):
    """评论点赞记录"""
    __tablename__ = 'comment_likes'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    comment_id = db.Column(UUIDType, db.ForeignKey('video_comments.id'), nullable=False)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('comment_id', 'user_id', name='unique_comment_like'),
    )

class UserVideoProgress(db.Model):
    __tablename__ = 'user_video_progress'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    progress = db.Column(db.Float, default=0)  # 0-1之间的浮点数
    last_position = db.Column(db.Integer, default=0)  # 上次观看位置（秒）
    completed = db.Column(db.Boolean, default=False)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'video_id', name='uq_user_video'),
    )

class Document(db.Model):
    """课程文档资料"""
    __tablename__ = 'documents'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4, comment='文档ID')
    title = db.Column(db.String(255), nullable=False, comment='文档标题')
    file_url = db.Column(db.String(255), nullable=False, comment='文件URL')
    file_type = db.Column(db.String(50), nullable=False, comment='文件类型')
    file_size = db.Column(db.Integer, default=0, comment='文件大小(字节)')
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False, comment='所属课程ID')
    upload_time = db.Column(db.DateTime, default=datetime.now, comment='上传时间')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否删除')

class VideoSummary(db.Model):
    __tablename__ = 'video_summaries'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False, unique=True)
    keywords = db.Column(db.String(255))  # 逗号分隔的关键词
    sections = db.Column(db.Text)  # JSON格式存储的章节摘要
    whole_summary = db.Column(db.Text)  # 整体摘要
    generate_time = db.Column(db.DateTime, default=datetime.now)
    
    def set_sections(self, sections_list):
        self.sections = json.dumps(sections_list)
        
    def get_sections(self):
        return json.loads(self.sections) if self.sections else []

class StudentCourseEnrollment(db.Model):
    __tablename__ = 'student_course_enrollments'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    student_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False)
    enroll_time = db.Column(db.DateTime, default=datetime.now)
    
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course'),
    )

class UserPermission(db.Model):
    __tablename__ = 'user_permission'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    course_access = db.Column(db.Text, nullable=True)  # JSON格式的课程ID列表
    comment_enabled = db.Column(db.Boolean, default=True)
    download_enabled = db.Column(db.Boolean, default=False)
    update_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关联用户 - 修改为使用back_populates
    user = db.relationship('Users', back_populates='permissions')
    
    def set_course_access(self, course_ids):
        """设置可访问课程ID列表"""
        self.course_access = json.dumps(course_ids)
    
    def get_course_access(self):
        """获取可访问课程ID列表"""
        if not self.course_access:
            return []
        try:
            return json.loads(self.course_access)
        except:
            return []

class VideoProcessingTask(db.Model):
    """视频处理任务模型"""
    __tablename__ = 'video_processing_tasks'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False, comment='关联的视频ID')
    task_id = db.Column(db.String(50), nullable=False, comment='处理任务ID')
    status = db.Column(db.String(20), nullable=False, comment='处理状态：pending, processing, completed, failed')
    processing_type = db.Column(db.String(20), nullable=False, comment='处理类型：transcoding, thumbnail, subtitle, all')
    progress = db.Column(db.Float, default=0.0, comment='处理进度，0-100')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    start_time = db.Column(db.DateTime, default=datetime.now, nullable=False, comment='开始时间')
    end_time = db.Column(db.DateTime, nullable=True, comment='结束时间')
    
    # 修改关系定义，使用back_populates对应Video中的processing_tasks
    video = db.relationship('Video', back_populates='processing_tasks')

class VideoKeyframe(db.Model):
    """存储视频关键帧及其OCR/ASR信息"""
    __tablename__ = 'video_keyframes'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    time_point = db.Column(db.Float, nullable=False)  # 秒
    time_formatted = db.Column(db.String(20))
    file_name = db.Column(db.String(255))
    ocr_result = db.Column(db.Text)  # 存储OCR识别到的文本
    asr_texts = db.Column(db.Text)  # 存储ASR识别到的文本
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    video = db.relationship('Video', backref=db.backref('keyframes', lazy='dynamic'))
    
    def set_ocr_result(self, ocr_list):
        self.ocr_result = json.dumps(ocr_list, ensure_ascii=False)
        
    def get_ocr_result(self):
        return json.loads(self.ocr_result) if self.ocr_result else []

class VideoVectorIndex(db.Model):
    """存储视频向量索引的信息"""
    __tablename__ = 'video_vector_indices'
    
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    index_path = db.Column(db.String(255), nullable=False)  # 存储索引文件路径
    embedding_model = db.Column(db.String(100))  # 使用的嵌入模型
    total_vectors = db.Column(db.Integer, default=0)
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    video = db.relationship('Video', backref=db.backref('vector_indices', lazy='dynamic'))

class TaskLog(db.Model):
    __tablename__ = 'task_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(50), index=True)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), index=True)  # 添加外键关联到videos表
    log_level = db.Column(db.String(20))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    # 可选：添加关系，方便通过log获取video对象
    video = db.relationship('Video', backref=db.backref('task_logs', lazy='dynamic'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'video_id': str(self.video_id) if self.video_id else None,
            'log_level': self.log_level,
            'message': self.message,
            'timestamp': self.timestamp.isoformat()
        }

# 聊天会话模型
class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUIDType, db.ForeignKey('users.id'), nullable=False)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=True)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = db.Column(db.Boolean, default=False)
    
    # 关联关系
    user = db.relationship('Users', backref='chat_sessions')
    video = db.relationship('Video', backref='chat_sessions')
    course = db.relationship('Course', backref='chat_sessions')
    messages = db.relationship('ChatMessage', backref='session', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'video_id': str(self.video_id) if self.video_id else None,
            'course_id': str(self.course_id) if self.course_id else None,
            'title': self.title,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'message_count': len(self.messages) if self.messages else 0
        }

# 聊天消息模型
class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUIDType, db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # user 或 assistant
    content = db.Column(db.Text, nullable=False)
    time_references = db.Column(db.Text, nullable=True)  # 存储引用的视频时间点，JSON字符串
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_time_references(self, references):
        """设置时间引用点"""
        if references is None:
            self.time_references = None
        else:
            self.time_references = json.dumps(references)
    
    def get_time_references(self):
        """获取时间引用点"""
        if not self.time_references:
            return None
        try:
            return json.loads(self.time_references)
        except:
            return None
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'session_id': str(self.session_id),
            'role': self.role,
            'content': self.content,
            'time_references': self.get_time_references(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# 知识图谱相关模型

class Keyword(db.Model):
    """关键词模型 - 存储所有关键词"""
    __tablename__ = 'keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False, unique=True, comment='关键词名称')
    category = db.Column(db.String(50), nullable=False, comment='关键词分类：core_concept, main_module, specific_point')
    description = db.Column(db.Text, nullable=True, comment='关键词描述')
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    video_keywords = db.relationship('VideoKeyword', back_populates='keyword', lazy='dynamic')
    course_keywords = db.relationship('CourseKeyword', back_populates='keyword', lazy='dynamic')
    keyword_relations_source = db.relationship('KeywordRelation', 
                                             foreign_keys='KeywordRelation.source_keyword_id',
                                             back_populates='source_keyword', lazy='dynamic')
    keyword_relations_target = db.relationship('KeywordRelation',
                                             foreign_keys='KeywordRelation.target_keyword_id', 
                                             back_populates='target_keyword', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }

class VideoKeyword(db.Model):
    """视频关键词关系表"""
    __tablename__ = 'video_keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    video_id = db.Column(UUIDType, db.ForeignKey('videos.id'), nullable=False)
    keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    weight = db.Column(db.Float, default=1.0, comment='关键词在视频中的重要程度')
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    video = db.relationship('Video', backref='video_keywords')
    keyword = db.relationship('Keyword', back_populates='video_keywords')
    
    __table_args__ = (
        db.UniqueConstraint('video_id', 'keyword_id', name='uq_video_keyword'),
    )

class CourseKeyword(db.Model):
    """课程关键词关系表"""
    __tablename__ = 'course_keywords'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False)
    keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    video_count = db.Column(db.Integer, default=0, comment='包含该关键词的视频数量')
    avg_weight = db.Column(db.Float, default=0.0, comment='该关键词在课程中的平均权重')
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    course = db.relationship('Course', backref='course_keywords')
    keyword = db.relationship('Keyword', back_populates='course_keywords')
    
    __table_args__ = (
        db.UniqueConstraint('course_id', 'keyword_id', name='uq_course_keyword'),
    )

class KeywordRelation(db.Model):
    """关键词关系表 - 存储关键词之间的关系"""
    __tablename__ = 'keyword_relations'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    source_keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    target_keyword_id = db.Column(UUIDType, db.ForeignKey('keywords.id'), nullable=False)
    relation_type = db.Column(db.String(50), nullable=False, comment='关系类型：prerequisite, related, contains等')
    strength = db.Column(db.Float, default=1.0, comment='关系强度 0-1')
    description = db.Column(db.Text, nullable=True, comment='关系描述')
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    source_keyword = db.relationship('Keyword', 
                                   foreign_keys=[source_keyword_id],
                                   back_populates='keyword_relations_source')
    target_keyword = db.relationship('Keyword',
                                   foreign_keys=[target_keyword_id], 
                                   back_populates='keyword_relations_target')
    
    __table_args__ = (
        db.UniqueConstraint('source_keyword_id', 'target_keyword_id', 'relation_type', 
                          name='uq_keyword_relation'),
    )
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'source_keyword_id': str(self.source_keyword_id),
            'target_keyword_id': str(self.target_keyword_id),
            'relation_type': self.relation_type,
            'strength': self.strength,
            'description': self.description
        }

class KnowledgeGraphProcessingTask(db.Model):
    """知识图谱处理任务表"""
    __tablename__ = 'knowledge_graph_tasks'
    
    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUIDType, db.ForeignKey('courses.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False, comment='任务类型：keyword_extraction, categorization, relation_building')
    status = db.Column(db.String(20), nullable=False, default='pending', comment='任务状态：pending, processing, completed, failed')
    progress = db.Column(db.Float, default=0.0, comment='处理进度 0-1')
    result_data = db.Column(db.Text, nullable=True, comment='处理结果JSON数据')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.now)
    
    # 关系
    course = db.relationship('Course', backref='knowledge_graph_tasks')
    
    def set_result_data(self, data):
        """设置结果数据"""
        self.result_data = json.dumps(data, ensure_ascii=False)
    
    def get_result_data(self):
        """获取结果数据"""
        if not self.result_data:
            return {}
        try:
            return json.loads(self.result_data)
        except:
            return {}
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'course_id': str(self.course_id),
            'task_type': self.task_type,
            'status': self.status,
            'progress': self.progress,
            'result_data': self.get_result_data(),
            'error_message': self.error_message,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
