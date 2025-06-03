"""检索器服务模块"""
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from config.qa_config import QAConfig


class RetrieverService:
    """检索器服务"""
    
    @staticmethod
    def create_ensemble_retriever(index):
        """创建混合检索器：结合关键词匹配和语义检索"""
        # 获取所有文档用于BM25
        all_docs = []
        for i in range(index.index.ntotal):
            try:
                # 从FAISS索引中获取文档
                doc_id = index.index_to_docstore_id[i]
                doc = index.docstore.search(doc_id)
                if doc:
                    all_docs.append(doc)
            except:
                continue
        
        # 创建BM25检索器（适合关键词匹配）
        bm25_retriever = BM25Retriever.from_documents(
            all_docs, 
            k=QAConfig.BM25_K
        )
        
        # 创建语义检索器（适合语义理解）
        semantic_retriever = index.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": QAConfig.SEMANTIC_K, 
                "score_threshold": QAConfig.SEMANTIC_SCORE_THRESHOLD,
                "fetch_k": QAConfig.SEMANTIC_FETCH_K
            }
        )
        
        # 混合检索器：结合关键词匹配和语义检索
        retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, semantic_retriever],
            weights=QAConfig.ENSEMBLE_WEIGHTS,
            k=QAConfig.ENSEMBLE_K
        )
        
        return retriever


# 全局检索器服务实例
retriever_service = RetrieverService()
