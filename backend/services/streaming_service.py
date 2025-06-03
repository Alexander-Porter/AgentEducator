"""流式响应处理服务模块"""
import json
import traceback
from queue import Queue
from threading import Thread
from flask import current_app
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from .llm_service import llm_service
from .memory_service import memory_service
from .callbacks import OptimizedStreamingCallback, CustomStreamingCallback, StatusNotifier
from .chat_service import chat_service
from .qa_chain_service import qa_chain_service
from .source_service import source_service


class StreamingService:
    """流式响应处理服务"""
    
    def create_general_stream_generator(self, query, session_id, history):
        """创建通用模式的流式生成器"""
        queue = Queue()
        answer_content = ""
        
        def generate():
            nonlocal answer_content
            
            callback = OptimizedStreamingCallback(queue)
            callback.answer_content = answer_content  # 同步引用
            
            llm = llm_service.create_general_chat_llm(streaming=True, callback=callback)
            app = current_app._get_current_object()
            
            def process_query():
                nonlocal answer_content
                try:
                    # 状态通知
                    notifier = StatusNotifier(queue)
                    notifier.notify_analysis_start()
                    
                    # 构建聊天历史
                    chat_history = memory_service.format_chat_history(history)
                    
                    notifier.notify_generation_start()
                    
                    prompt = ChatPromptTemplate.from_template(
                        """你是一名教育内容讲解助手，请基于你的知识回答用户的问题。
由于这是通用模式下没有参考文档，你不需要添加引用标记。
如果不确定，请坦率说明你不知道。

聊天历史:
{chat_history}

用户问题: {question}"""
                    )
                    
                    formatted_prompt = prompt.format_messages(
                        chat_history=chat_history,
                        question=query
                    )
                      # 流式处理
                    for chunk in llm.stream(formatted_prompt):
                        if hasattr(chunk, 'content'):
                            pass  # callback已经处理了token
                    
                    # 确保缓冲区被完全刷新
                    callback.flush_remaining_buffer()
                    
                    # 同步最终答案内容
                    answer_content = callback.answer_content
                    
                    queue.put("[END]")
                    
                    # 保存AI回复
                    with app.app_context():
                        if chat_service.save_message_to_db(session_id, 'assistant', answer_content):
                            current_app.logger.info(f"通用模式回复已保存，token数: {callback.token_count}")
                    
                    queue.put(json.dumps({
                        "sources": [], 
                        "session": {"sessionId": str(session_id)},
                        "stats": {"tokens": callback.token_count}
                    }))
                    
                except Exception as e:
                    with app.app_context():
                        current_app.logger.error(f"通用模式处理失败: {str(e)}")
                    
                    # 保存错误回复
                    if answer_content.strip():
                        error_content = answer_content + f"\n\n[处理过程中出现错误: {str(e)}]"
                        with app.app_context():
                            chat_service.save_message_to_db(session_id, 'assistant', error_content)
                    
                    queue.put(f"处理请求失败: {str(e)}")
                    queue.put("[END]")
                    queue.put(json.dumps({
                        "sources": [], 
                        "session": {"sessionId": str(session_id)},
                        "error": str(e)
                    }))
            
            Thread(target=process_query, daemon=True).start()
            
            while True:
                token = queue.get()
                if token == "[END]":
                    sources_json = queue.get()
                    yield f"data: {sources_json}\n\n"
                    break
                
                # 处理换行符和特殊字符
                if token == "\n":
                    yield "data: \n\n"
                else:
                    if '\n' in token:
                        parts = token.split('\n')
                        for i, part in enumerate(parts):
                            if i > 0:
                                yield "data: \n\n"
                            if part:
                                safe_part = part.replace('\r', '\\r')
                                yield f"data: {safe_part}\n\n"
                    else:
                        safe_token = token.replace('\r', '\\r')
                        yield f"data: {safe_token}\n\n"
        
        return generate
    
    def create_rag_stream_generator(self, query, session_id, history, video_id, course_id, index):
        """创建RAG模式的流式生成器"""
        queue = Queue()
        answer_content = ""
        sources = []
        
        def generate():
            nonlocal answer_content, sources
            
            callback = CustomStreamingCallback(queue)
            callback.answer_content = answer_content  # 同步引用
            
            app = current_app._get_current_object()
            
            def process_query():
                nonlocal answer_content, sources
                try:
                    # 状态通知
                    notifier = StatusNotifier(queue)
                    notifier.notify_retrieval_start()
                    
                    qa_chain, error2 = qa_chain_service.create_qa_chain(video_id, course_id, index, history, callback)
                    if error2:
                        queue.put(f"错误: {error2}")
                        queue.put("[END]")
                        queue.put(json.dumps({
                            "sources": [], 
                            "session": {"sessionId": str(session_id)},
                            "error": error2
                        }))
                        return
                    
                    # 检索完成通知
                    doc_count = index.index.ntotal if index and hasattr(index, 'index') and hasattr(index.index, 'ntotal') else 0
                    notifier.notify_retrieval_complete(doc_count)
                    notifier.notify_question_analysis()
                    result = qa_chain.invoke({"question": query})
                    
                    notifier.notify_generation_start()
                    
                    # 确保缓冲区被完全刷新
                    callback.flush_remaining_buffer()
                    
                    # 同步最终答案内容
                    answer_content = callback.answer_content
                    
                    # 处理源文档
                    if not isinstance(qa_chain, LLMChain) and "source_documents" in result:
                        source_docs = result["source_documents"]
                        sources = source_service.process_source_documents(source_docs, video_id, app)
                    
                    # 保存AI回复
                    with app.app_context():
                        if chat_service.save_message_to_db(session_id, 'assistant', answer_content, sources):
                            current_app.logger.info(f"RAG模式回复已保存，token数: {callback.token_count}, 引用数: {len(sources)}")
                        current_app.logger.info(f"检索到 {len(sources)} 个源文档，按顺序编号为引用角标")
                    
                    queue.put("[END]")
                    queue.put(json.dumps({
                        "sources": sources, 
                        "session": {"sessionId": str(session_id)},
                        "stats": {"tokens": callback.token_count, "sources": len(sources)}
                    }))
                    
                except Exception as e:
                    with app.app_context():
                        current_app.logger.error(f"RAG模式处理失败: {str(e)}")
                    print(traceback.format_exc())
                    
                    # 保存错误回复
                    if answer_content.strip():
                        error_content = answer_content + f"\n\n[处理过程中出现错误: {str(e)}]"
                        with app.app_context():
                            chat_service.save_message_to_db(session_id, 'assistant', error_content)
                    else:
                        with app.app_context():
                            from models.models import db
                            db.session.rollback()
                    
                    queue.put(f"处理请求失败: {str(e)}")
                    queue.put("[END]")
                    queue.put(json.dumps({
                        "sources": [], 
                        "session": {"sessionId": str(session_id)},
                        "error": str(e)
                    }))
            
            Thread(target=process_query, daemon=True).start()
            
            while True:
                token = queue.get()
                if token == "[END]":
                    sources_json = queue.get()
                    yield f"data: {sources_json}\n\n"
                    break
                
                # 处理换行符和特殊字符
                if token == "\n":
                    yield "data: \n\n"
                else:
                    if '\n' in token:
                        parts = token.split('\n')
                        for i, part in enumerate(parts):
                            if i > 0:
                                yield "data: \n\n"
                            if part:
                                safe_part = part.replace('\r', '\\r')
                                yield f"data: {safe_part}\n\n"
                    else:
                        safe_token = token.replace('\r', '\\r')
                        yield f"data: {safe_token}\n\n"
        
        return generate


# 全局流式服务实例
streaming_service = StreamingService()
