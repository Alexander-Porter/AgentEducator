"""嵌入模型服务模块"""
from langchain_openai import OpenAIEmbeddings
from config.qa_config import QAConfig


class EmbeddingsService:
    """嵌入模型服务（单例模式）"""
    
    _instance = None
    _embeddings = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_embeddings(self):
        """获取嵌入模型"""
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                openai_api_key=QAConfig.API_KEY,
                base_url=QAConfig.SILICON_API_BASE,
                model=QAConfig.EMBEDDING_MODEL
            )
        return self._embeddings


# 全局实例
embeddings_service = EmbeddingsService()
