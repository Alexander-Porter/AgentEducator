"""源文档处理服务模块"""
from flask import current_app
from .cache_service import get_video_info


class SourceService:
    """源文档处理服务"""
    
    @staticmethod
    def process_source_documents(source_docs, video_id, app):
        """处理检索到的源文档，生成引用信息"""
        sources = []
        
        for idx, doc in enumerate(source_docs):
            if hasattr(doc, "metadata"):
                time_point = doc.metadata.get("time_point", 0)
                doc_video_id = doc.metadata.get("video_id", video_id)
                
                with app.app_context():
                    video_title, this_course_id = get_video_info(doc_video_id)
                
                # 使用检索结果的顺序作为引用编号 (1-based)
                source_item = {
                    "index": idx + 1,  # 这个index对应AI回答中的引用角标
                    "video_id": str(doc_video_id),
                    "video_title": video_title,
                    "course_id": str(this_course_id) if this_course_id else None,
                    "course_title": doc.metadata.get("course_title", ""),
                    "time_point": time_point,
                    "time_formatted": f"{int(time_point // 60):02d}:{int(time_point % 60):02d}",
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                }
                sources.append(source_item)
        
        return sources


# 全局源文档服务实例
source_service = SourceService()
