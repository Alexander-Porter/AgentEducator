"""向量索引服务模块"""
import os
import time
import traceback
from flask import current_app, has_app_context
from langchain_community.vectorstores import FAISS
from models.models import VideoVectorIndex, Video, db
from .embeddings_service import embeddings_service
from .cache_service import cache_service


class IndexService:
    """向量索引服务"""
    
    def get_video_index(self, video_id):
        """获取指定视频的向量索引（带缓存）"""
        cache_key = f"video_{video_id}"
        
        if cache_service.has_cached_index(cache_key):
            if has_app_context():
                current_app.logger.debug(f"使用缓存的视频索引: {video_id}")
            return cache_service.get_cached_index(cache_key), None
        
        if not has_app_context():
            from app import create_app
            app = create_app()
            app_ctx = app.app_context()
            app_ctx.push()
            try:
                result = self._get_video_index_impl(video_id)
                if result[0] is not None:  # 成功加载则缓存
                    cache_service.set_index_cache(cache_key, result[0])
                return result
            finally:
                app_ctx.pop()
        else:
            result = self._get_video_index_impl(video_id)
            if result[0] is not None:  # 成功加载则缓存
                cache_service.set_index_cache(cache_key, result[0])
            return result

    def get_course_video_index(self, course_id):
        """获取指定课程的向量索引（带缓存）"""
        cache_key = f"course_{course_id}"
        
        if cache_service.has_cached_index(cache_key):
            if has_app_context():
                current_app.logger.debug(f"使用缓存的课程索引: {course_id}")
            return cache_service.get_cached_index(cache_key), None
        
        if not has_app_context():
            from app import create_app
            app = create_app()
            app_ctx = app.app_context()
            app_ctx.push()
            try:
                result = self._get_course_video_index_impl(course_id)
                if result[0] is not None:  # 成功加载则缓存
                    cache_service.set_index_cache(cache_key, result[0])
                return result
            finally:
                app_ctx.pop()
        else:
            result = self._get_course_video_index_impl(course_id)
            if result[0] is not None:  # 成功加载则缓存
                cache_service.set_index_cache(cache_key, result[0])
            return result
    
    def merge_course_indices(self, course_ids):
        """合并多个课程的所有视频向量索引（优化版）"""
        cache_key = f"multi_course_{'_'.join(map(str, sorted(course_ids)))}"
        
        if cache_service.has_cached_index(cache_key):
            if has_app_context():
                current_app.logger.debug(f"使用缓存的多课程索引")
            return cache_service.get_cached_index(cache_key), None
        
        try:
            start_time = time.time()
            embeddings = embeddings_service.get_embeddings()
            base_index = None
            total_loaded = 0
            
            # 批量查询所有相关的视频和索引
            videos_with_indices = db.session.query(Video, VideoVectorIndex).join(
                VideoVectorIndex, Video.id == VideoVectorIndex.video_id
            ).filter(Video.course_id.in_(course_ids),
                    Video.is_deleted.is_(False)
                     ).all()
            
            if has_app_context():
                current_app.logger.info(f"找到 {len(videos_with_indices)} 个视频索引待合并")
            
            for video, index_info in videos_with_indices:
                if not os.path.exists(index_info.index_path):
                    continue
                
                try:
                    current_index = FAISS.load_local(
                        index_info.index_path, 
                        embeddings, 
                        allow_dangerous_deserialization=True
                    )
                    
                    if base_index is None:
                        base_index = current_index
                    else:
                        base_index.merge_from(current_index)
                    
                    total_loaded += 1
                except Exception as e:
                    if has_app_context():
                        current_app.logger.error(f"加载视频 {video.id} 索引失败: {str(e)}")
                    continue
            
            if base_index is None:
                return None, "未找到任何有效的索引"
            
            # 缓存结果
            cache_service.set_index_cache(cache_key, base_index)
            
            load_time = time.time() - start_time
            if has_app_context():
                current_app.logger.info(f"成功合并 {total_loaded} 个索引，耗时 {load_time:.2f}s")
            return base_index, None
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"合并索引失败: {str(e)}")
                traceback.print_exc()
            return None, f"合并索引失败: {str(e)}"
    
    def _get_course_video_index_impl(self, course_id):
        """实际获取课程视频索引的实现（优化版）"""
        try:
            start_time = time.time()
            embeddings = embeddings_service.get_embeddings()
            
            # 批量查询视频和索引信息
            videos_with_indices = db.session.query(Video, VideoVectorIndex).join(
                VideoVectorIndex, Video.id == VideoVectorIndex.video_id
            ).filter(Video.course_id == course_id,
                     Video.is_deleted.is_(False)).all()
            
            if not videos_with_indices:
                return None, f"课程 {course_id} 没有可用的视频索引"
            
            if has_app_context():
                current_app.logger.info(f"课程 {course_id} 有 {len(videos_with_indices)} 个有效视频索引")
            
            base_index = None
            loaded_count = 0
            
            for video, index_info in videos_with_indices:
                if not os.path.exists(index_info.index_path):
                    if has_app_context():
                        current_app.logger.warning(f"索引文件不存在: {index_info.index_path}")
                    continue
                
                try:
                    current_index = FAISS.load_local(
                        index_info.index_path, 
                        embeddings, 
                        allow_dangerous_deserialization=True
                    )
                    
                    if base_index is None:
                        base_index = current_index
                    else:
                        base_index.merge_from(current_index)
                    
                    loaded_count += 1
                    if has_app_context():
                        current_app.logger.debug(f"成功加载视频 {video.id} 的索引")
                except Exception as e:
                    if has_app_context():
                        current_app.logger.error(f"加载视频 {video.id} 索引失败: {str(e)}")
                    continue
            
            if base_index is None:
                return None, "未找到任何有效的视频索引"
            
            load_time = time.time() - start_time
            if has_app_context():
                current_app.logger.info(f"成功合并课程 {course_id} 的 {loaded_count} 个索引，耗时 {load_time:.2f}s")
            return base_index, None
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"获取课程索引失败: {str(e)}")
                traceback.print_exc()
            return None, f"获取课程索引失败: {str(e)}"

    def _get_video_index_impl(self, video_id):
        """实际获取视频索引的实现（优化版）"""
        try:
            # 查询数据库获取索引信息
            index_info = VideoVectorIndex.query.filter_by(video_id=video_id).first()
            if not index_info:
                return None, "视频索引不存在，请先处理视频"
                
            # 检查索引路径是否存在
            if not os.path.exists(index_info.index_path):
                return None, f"索引文件不存在: {index_info.index_path}"
                
            # 加载索引
            embeddings = embeddings_service.get_embeddings()
            index = FAISS.load_local(
                index_info.index_path, 
                embeddings, 
                allow_dangerous_deserialization=True
            )
            return index, None
            
        except Exception as e:
            if has_app_context():
                current_app.logger.error(f"加载索引失败: {str(e)}")
            return None, f"加载索引失败: {str(e)}"


# 全局索引服务实例
index_service = IndexService()
