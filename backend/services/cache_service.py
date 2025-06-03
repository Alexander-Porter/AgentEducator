"""缓存服务模块"""
from functools import lru_cache
from flask import has_app_context
from config.qa_config import QAConfig
from models.models import Video, Course, Keyword, VideoKeyword, CourseKeyword,VideoSummary
from sqlalchemy.orm import joinedload


class CacheService:
    """缓存服务"""
    
    def __init__(self):
        # 索引缓存
        self._index_cache = {}
    
    def get_index_cache(self):
        """获取索引缓存"""
        return self._index_cache
    
    def set_index_cache(self, key, value):
        """设置索引缓存"""
        self._index_cache[key] = value
    
    def get_cached_index(self, key):
        """获取缓存的索引"""
        return self._index_cache.get(key)
    
    def has_cached_index(self, key):
        """检查是否有缓存的索引"""
        return key in self._index_cache


# 视频信息缓存装饰器
@lru_cache(maxsize=QAConfig.LRU_CACHE_SIZE)
def get_video_info(video_id):
    """缓存视频信息查询"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            video = Video.query.filter_by(id=video_id).first()
            return (video.title, video.course_id) if video else (None, None)
    else:
        video = Video.query.filter_by(id=video_id).first()
        return (video.title, video.course_id) if video else (None, None)


# 课程信息缓存装饰器
@lru_cache(maxsize=QAConfig.LRU_CACHE_SIZE)
def get_course_info(course_id):
    """缓存课程信息查询"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            course = Course.query.filter_by(id=course_id).first()
            return course.name if course else None
    else:
        course = Course.query.filter_by(id=course_id).first()
        return course.name if course else None


# 视频关键词缓存装饰器
@lru_cache(maxsize=QAConfig.LRU_CACHE_SIZE)
def get_video_keywords(video_id, limit=20):
    """缓存视频关键词查询，返回按权重排序的前N个关键词"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return _get_video_keywords_impl(video_id, limit)
    else:
        return _get_video_keywords_impl(video_id, limit)

@lru_cache(maxsize=QAConfig.LRU_CACHE_SIZE)
def get_video_summary(video_id):
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            video_summary = VideoSummary.query.filter_by(video_id=video_id).first()
            return video_summary.whole_summary if video_summary else None

def _get_video_keywords_impl(video_id, limit):
    """获取视频关键词的实际实现"""
    video_keywords = (VideoKeyword.query
                      .filter_by(video_id=video_id)
                      .join(Keyword)
                      .with_entities(Keyword.name, VideoKeyword.weight)
                      .order_by(VideoKeyword.weight.desc())
                      .limit(limit)
                      .all())
    
    return [{"name": kw.name, "weight": kw.weight} for kw in video_keywords] if video_keywords else []


# 课程关键词缓存装饰器  
@lru_cache(maxsize=QAConfig.LRU_CACHE_SIZE)
def get_course_keywords(course_id, limit=10):
    """缓存课程关键词查询，返回按重要性排序的前N个关键词"""
    if not has_app_context():
        from app import create_app
        app = create_app()
        with app.app_context():
            return _get_course_keywords_impl(course_id, limit)
    else:
        return _get_course_keywords_impl(course_id, limit)


def _get_course_keywords_impl(course_id, limit):
    """获取课程关键词的实际实现"""
    course_keywords = (CourseKeyword.query
                       .filter_by(course_id=course_id)
                       .join(Keyword)
                       .with_entities(
                           Keyword.name, 
                           Keyword.category,
                           CourseKeyword.video_count,
                           CourseKeyword.avg_weight
                       )
                       .order_by(
                           CourseKeyword.video_count.desc(),
                           CourseKeyword.avg_weight.desc()
                       )
                       .limit(limit)
                       .all())
    
    return [{"name": kw.name, "category": kw.category, "video_count": kw.video_count, "avg_weight": kw.avg_weight} 
            for kw in course_keywords] if course_keywords else []


# 全局缓存实例
cache_service = CacheService()
