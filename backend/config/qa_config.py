"""QA系统配置模块"""
import os


class QAConfig:
    """QA系统配置类"""
    
    # API配置
    SILICON_API_BASE = "https://api.siliconflow.cn/v1"
    API_KEY = os.environ.get("OPENAI_API_KEY", "sk-ddoozzdqdeuxptrdxyhohdpkcjikxemkpxdcbhzlnfxahbts")
    
    # 模型配置
    EMBEDDING_MODEL = 'Pro/BAAI/bge-m3'
    CHAT_MODEL = "Pro/deepseek-ai/DeepSeek-V3"
    GENERAL_CHAT_MODEL = "Qwen/Qwen3-8B"
    
    # 向量索引配置
    VECTOR_INDEX_DIR = "vector_indices"
    
    # 检索配置
    BM25_K = 3
    SEMANTIC_K = 4
    SEMANTIC_SCORE_THRESHOLD = 0.3
    SEMANTIC_FETCH_K = 10
    ENSEMBLE_WEIGHTS = [0.4, 0.6]  # BM25权重0.4，语义检索权重0.6
    ENSEMBLE_K = 10
    
    # LLM配置
    TEMPERATURE = 0.7
    REQUEST_TIMEOUT = 60
    
    # 历史消息配置
    MAX_HISTORY_LENGTH = 10
    RECENT_HISTORY_LENGTH = 8
    
    # 缓存配置
    LRU_CACHE_SIZE = 100
