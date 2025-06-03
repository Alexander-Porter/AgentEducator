"""LLM服务模块"""
from langchain_openai import ChatOpenAI
from config.qa_config import QAConfig


class LLMService:
    """LLM服务"""
    
    @staticmethod
    def create_chat_llm(streaming=False, callback=None):
        """创建聊天LLM实例"""
        return ChatOpenAI(
            openai_api_key=QAConfig.API_KEY,
            openai_api_base=QAConfig.SILICON_API_BASE,
            temperature=QAConfig.TEMPERATURE,
            model=QAConfig.CHAT_MODEL,
            streaming=streaming,
            callbacks=[callback] if callback else None,
            request_timeout=QAConfig.REQUEST_TIMEOUT
        )
    
    @staticmethod
    def create_general_chat_llm(streaming=False, callback=None):
        """创建通用聊天LLM实例"""
        return ChatOpenAI(
            openai_api_key=QAConfig.API_KEY,
            openai_api_base=QAConfig.SILICON_API_BASE,
            temperature=QAConfig.TEMPERATURE,
            model=QAConfig.GENERAL_CHAT_MODEL,
            streaming=streaming,
            callbacks=[callback] if callback else None,
            request_timeout=QAConfig.REQUEST_TIMEOUT
        )
    
    @staticmethod
    def create_non_streaming_llm():
        """创建非流式LLM实例（用于问题重写）"""
        return ChatOpenAI(
            openai_api_key=QAConfig.API_KEY,
            openai_api_base=QAConfig.SILICON_API_BASE,
            temperature=QAConfig.TEMPERATURE,
            model=QAConfig.CHAT_MODEL,
            streaming=False,
            request_timeout=QAConfig.REQUEST_TIMEOUT
        )


# 全局LLM服务实例
llm_service = LLMService()
