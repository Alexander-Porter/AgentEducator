"""
向量索引模块
负责构建和管理视频关键帧的向量索引
"""

import os
from flask import current_app
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# 导入数据库模型
from models.models import VideoVectorIndex

def build_vector_index(video_id, keyframes_data, index_path, api_key=None, base_url=None, model='Pro/BAAI/bge-m3'):
    """
    构建视频关键帧的向量索引
    
    参数:
        video_id: 视频ID
        keyframes_data: 关键帧数据列表
        index_path: 索引保存路径
        api_key: API密钥，默认为None，将使用环境变量中的API_KEY
        base_url: API基础URL，默认为None，将使用环境变量中的SILICON_API_BASE
        model: 嵌入模型名称，默认为'Pro/BAAI/bge-m3'
        
    返回:
        bool: 索引构建是否成功
    """
    try:
        # 获取API配置
        if api_key is None:
            import os
            api_key = os.environ.get("OPENAI_API_KEY")
        if base_url is None:
            base_url = os.environ.get("SILICON_API_BASE", "https://api.siliconflow.cn/v1")
        
        # 初始化embeddings
        embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            base_url=base_url,
            model=model
        )
        
        # 准备文档和元数据
        docs = []
        metadatas = []
        
        for keyframe in keyframes_data:
            # 合并OCR和ASR文本
            ocr_text = " ".join(keyframe.get("ocr_result", []))
            asr_text = keyframe.get("asr_texts", "")
            combined_text = f"屏幕内容：{ocr_text}\n教师口述：{asr_text}".strip()
            
            if combined_text:
                docs.append(combined_text)
                metadatas.append({
                    "video_id": str(video_id),
                    "keyframe_id": keyframe["id"],
                    "frame_number": keyframe["frame_number"],
                    "time_point": keyframe["time_point"],
                    "time_formatted": keyframe["time_formatted"],
                    "file_name": keyframe["file_name"]
                })
        
        # 分批处理，避免内存问题
        MAX_BATCH_SIZE = 64
        
        # 构建索引
        if not docs:
            current_app.logger.warning("没有可索引的文本内容")
            return False
        
        index = None
        for i in range(0, len(docs), MAX_BATCH_SIZE):
            batch_docs = docs[i:i + MAX_BATCH_SIZE]
            batch_metadatas = metadatas[i:i + MAX_BATCH_SIZE]
            
            if index is None:
                index = FAISS.from_texts(
                    texts=batch_docs,
                    embedding=embeddings,
                    metadatas=batch_metadatas
                )
            else:
                batch_index = FAISS.from_texts(
                    texts=batch_docs,
                    embedding=embeddings,
                    metadatas=batch_metadatas
                )
                index.merge_from(batch_index)
        
        # 创建索引目录
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        
        # 保存索引
        index.save_local(index_path)
        
        return True
    except Exception as e:
        current_app.logger.error(f"构建向量索引失败: {str(e)}")
        return False

def check_vector_index_exists(video_id):
    """
    检查向量索引是否存在
    
    参数:
        video_id: 视频ID
        
    返回:
        (exists, index_path): 布尔值表示是否存在，若存在则返回索引路径
    """
    try:
        # 查询数据库中的向量索引记录
        vector_index = VideoVectorIndex.query.filter_by(video_id=video_id).first()
        
        if not vector_index:
            return False, None
            
        index_path = vector_index.index_path
        
        # 检查文件是否实际存在
        if not os.path.exists(index_path):
            current_app.logger.warning(f"向量索引记录存在，但文件不存在: {index_path}")
            return False, index_path
            
        return True, index_path
    except Exception as e:
        current_app.logger.error(f"检查向量索引失败: {str(e)}")
        return False, None