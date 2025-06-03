import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt'}

def allowed_file(filename):
    """
    检查文件扩展名是否被允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_video_file(filename):
    """
    检查视频文件扩展名是否被允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_document_file(filename):
    """
    检查文档文件扩展名是否被允许
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOCUMENT_EXTENSIONS

def save_file(file, file_type='image'):
    """
    保存上传的文件
    
    Args:
        file: FileStorage对象
        file_type: 文件类型 (image, video, document, avatar)
        
    Returns:
        保存后的文件URL路径
    """
    # 获取安全的文件名
    filename = secure_filename(file.filename)
    
    # 根据文件类型设置保存目录
    if file_type == 'image':
        upload_folder = 'temp_img'
    elif file_type == 'video':
        upload_folder = 'temp_video'
    elif file_type == 'document':
        upload_folder = 'temp_docs'
    elif file_type == 'avatar':
        upload_folder = 'temp_avatars'
    else:
        upload_folder = 'temp_uploads'
    
    # 确保目录存在
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # 保存文件
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    
    # 返回文件的URL路径
    return f"/{upload_folder}/{unique_filename}"
