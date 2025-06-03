from flask import Flask, send_from_directory
from models.models import db  # Import db from models
import os
# 导入 OpenMP 冲突修复
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from config import Config,DebugConfig
from flask_cors import CORS
import atexit

# 导入新的路由模块
from routes.task_logs import task_logs_bp
import dotenv
dotenv.load_dotenv()
def create_app(config_name='development'):
    app = Flask(__name__)
    if os.getenv('IS_DEBUG') == 'True':
        app.config.from_object(DebugConfig)
    else:
        app.config.from_object(Config)
    
    # Initialize the database with the app
    db.init_app(app)

    # 配置 CORS
    CORS(app, 
         origins=["http://localhost:5173", "https://winstar.snakekiss.com"],
         supports_credentials=True,
         allow_headers=["*"],
         expose_headers=["*"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])    # Create all database tables
    with app.app_context():
        db.create_all()
    
    # 注册蓝图
    from routes.user import user_bp
    from routes.course import course_bp
    from routes.upload import upload_bp
    from routes.video import video_bp
    from routes.summary import summary_bp
    from routes.qa_api import qa_bp
    from routes.student import student_bp
    from routes.student_management import student_management_bp    
    from routes.chat_history import chat_history_bp
    from routes.knowledge_graph import knowledge_graph_bp
    from routes.statistics import statistics_bp
    from routes.teacher_dashboard import teacher_dashboard_bp
    
    @app.route('/temp_img/<path:filename>')
    def serve_image(filename):
        return send_from_directory('temp_img', filename)
    
    # 添加用于访问上传的视频的路由
    @app.route('/temp_video/<path:filename>')
    def serve_video(filename):
        return send_from_directory('temp_video', filename)
        
    # 添加用于访问上传的文档的路由
    @app.route('/temp_docs/<path:filename>')
    def serve_document(filename):
        return send_from_directory('temp_docs', filename)

    # 添加用于访问上传的头像的路由
    @app.route('/temp_avatars/<path:filename>')
    def serve_avatar(filename):
        return send_from_directory('temp_avatars', filename)

    app.register_blueprint(user_bp, url_prefix='/api/auth')  # 认证相关接口
    app.register_blueprint(course_bp, url_prefix='/api/courses')  # 课程相关接口(复数形式)
    app.register_blueprint(upload_bp, url_prefix='/api/uploads')  # 上传相关接口(复数形式)
    app.register_blueprint(video_bp, url_prefix='/api/videos')  # 视频相关接口(复数形式)
    app.register_blueprint(summary_bp, url_prefix='/api/summaries')  # 总结相关接口(复数形式)
    app.register_blueprint(qa_bp, url_prefix='/api/qa')  # 问答相关接口
    app.register_blueprint(student_bp, url_prefix='/api/students')  # 学生相关接口(复数形式)
    app.register_blueprint(task_logs_bp, url_prefix='/api/task_logs')  # 任务日志相关接口
    app.register_blueprint(student_management_bp, url_prefix='/api/student_management')  # 学生管理相关接口
    app.register_blueprint(chat_history_bp, url_prefix='/api/chat_history')  # 聊天历史相关接口
    app.register_blueprint(knowledge_graph_bp)  # 知识图谱相关接口
    app.register_blueprint(statistics_bp, url_prefix='/api/statistics')  # 统计数据相关接口
    app.register_blueprint(teacher_dashboard_bp, url_prefix='/api/teacher')  # 教师仪表板相关接口
    
    # 添加静态文件路由，用于访问上传的图片# 初始化视频处理线程池
    from utils.video_processing_pool import video_processing_pool
    
    # 初始化知识图谱处理线程池
    from utils.knowledge_graph_processing_pool import knowledge_graph_processing_pool
    
    # 注册应用关闭时的清理函数
    atexit.register(lambda: video_processing_pool.shutdown(wait=True))
    atexit.register(lambda: knowledge_graph_processing_pool.shutdown(wait=True))
    
    # 设置app的全局线程信息字典
    app.PROCESSING_THREADS = {}
    # 启动前查找所有软删除的视频并清理相关数据
    # 注意：这里不能直接执行数据库查询，因为还在应用初始化阶段
    # 数据库查询需要在应用上下文中执行
    with app.app_context():
        from models.models import Video
        from datetime import datetime
        from models.models import VideoKeyframe, VideoVectorIndex
        # 现在可以执行数据库查询了
        deleted_videos = Video.query.filter_by(is_deleted=True).all()
        for video in deleted_videos:
            print(f"Found soft-deleted video: {video.title} (ID: {video.id})")
            
            video.update_time = datetime.now()
            # 删除对应的VideoKeyframe和VideoVectorIndex
            db.session.query(VideoKeyframe).filter_by(video_id=video.id).delete()
            db.session.query(VideoVectorIndex).filter_by(video_id=video.id).delete()
            # 删除视频文件
            try:
                video_path = os.path.join(os.getcwd(), video.video_url.lstrip('/'))
                if os.path.exists(video_path):
                    os.remove(video_path)
                    
                # 删除视频封面图
                if video.cover_url:
                    cover_path = os.path.join(os.getcwd(), video.cover_url.lstrip('/'))
                    if os.path.exists(cover_path):
                        os.remove(cover_path)
            except Exception as e:
                app.logger.error(f"删除视频文件失败: {str(e)}")
        
        # 提交数据库更改
        db.session.commit()
    
    return app

if __name__ == '__main__':
    app = create_app()  # Fix: store the returned app
    app.run(host='0.0.0.0', port=5000, debug=False)  # 修改运行参数
