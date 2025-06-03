"""问答链服务模块"""
import traceback
from flask import current_app, has_app_context
from langchain.chains import RetrievalQA, LLMChain, ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain as LLMChainForDocs
from .llm_service import llm_service
from .memory_service import memory_service
from .retriever_service import retriever_service
from .cache_service import get_video_info, get_course_info, get_video_keywords, get_course_keywords, get_video_summary


class NumberedStuffDocumentsChain(StuffDocumentsChain):
    """自定义文档组合链，支持文档编号"""
    
    def _get_inputs(self, docs, **kwargs):
        # 为文档添加编号
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            formatted_doc = f"教学片段{i}: {doc.page_content}"
            formatted_docs.append(formatted_doc)
        
        document_string = self.document_separator.join(formatted_docs)
        inputs = {self.document_variable_name: document_string}
        inputs.update(kwargs)
        return inputs


class QAChainService:
    """问答链服务"""
    
    def create_qa_chain(self, video_id, course_id, index, history=None, streaming_callback=None):
        """创建问答链（优化版）"""
        if not has_app_context():
            from app import create_app
            app = create_app()
            with app.app_context():
                return self._create_qa_chain_impl(video_id, course_id, index, history, streaming_callback)
        else:
            return self._create_qa_chain_impl(video_id, course_id, index, history, streaming_callback)

    def _create_qa_chain_impl(self, video_id, course_id, index, history=None, streaming_callback=None):
        """实际创建问答链的实现（优化版）"""
        try:
            # 初始化LLM
            llm = llm_service.create_chat_llm(
                streaming=streaming_callback is not None,
                callback=streaming_callback
            )
            
            # 创建内存对象
            memory = memory_service.create_memory_from_history(history)
            
            if index is None:
                # 通用LLM模式
                template = """你是一名教育内容讲解助手，请基于你的知识回答以下问题。
由于是通用模式下没有参考文档，你不需要添加引用标记。
如果不确定，请坦率说明你不知道。

问题: {question}

回答:"""
                
                prompt = PromptTemplate(
                    template=template,
                    input_variables=["question"]
                )
                
                qa_chain = LLMChain(
                    llm=llm,
                    prompt=prompt,
                    memory=memory,
                    output_key="result"
                )
            else:
                # RAG模式 - 根据是否有video_id或course_id来构建不同的prompt
                context_info = self._build_context_info(video_id, course_id)
                
                # 创建混合检索器
                retriever = retriever_service.create_ensemble_retriever(index)
                
                condense_question_prompt = PromptTemplate.from_template(
                    """根据历史对话和后续问题，将后续问题改写成独立的问题。如果用户要求你给出与某个她提到的概念有关的概念，将你的独立问题直接针对你确定的有关概念进行提问。
                    例如：用户在历史对话中提到过银行家算法，然后她问“哪些系统使用了这个算法？”，你可以将后续问题改写为“哪里提到了死锁避免的银行家算法？”。即：将有关的概念（这里是死锁避免）也写进问题中。

历史对话:
{chat_history}

后续问题: {question}

独立问题:"""
                )
                
                # 根据上下文信息构建不同的prompt模板
                if video_id and course_id:
                    # 视频聊天模式
                    qa_prompt_template = self._build_video_chat_prompt(context_info)
                elif course_id:
                    # 课程聊天模式
                    qa_prompt_template = self._build_course_chat_prompt(context_info)
                else:
                    # 默认RAG模式
                    qa_prompt_template = self._build_default_rag_prompt()
                
                qa_prompt = PromptTemplate.from_template(qa_prompt_template)
                
                # 创建文档组合链
                llm_chain = LLMChainForDocs(llm=llm, prompt=qa_prompt)
                
                document_combine_chain = NumberedStuffDocumentsChain(
                    llm_chain=llm_chain,
                    document_variable_name="context",
                    document_separator="\n\n"
                )
                
                # 为question_generator创建一个不带流式回调的LLM实例
                non_streaming_llm = llm_service.create_non_streaming_llm()
                
                qa_chain = ConversationalRetrievalChain(
                    retriever=retriever,
                    question_generator=LLMChain(llm=non_streaming_llm, prompt=condense_question_prompt),
                    combine_docs_chain=document_combine_chain,
                    memory=memory,
                    return_source_documents=True,
                    output_key="result"
                )
            
            return qa_chain, None
            
        except Exception as e:
            traceback.print_exc()
            if has_app_context():
                current_app.logger.error(f"创建问答链失败: {str(e)}")
            return None, f"创建问答链失败: {str(e)}"

    def _build_context_info(self, video_id, course_id):
        """构建上下文信息"""
        context = {}
        
        try:
            # 获取视频信息
            if video_id:
                video_title, video_course_id = get_video_info(video_id)
                if video_title:
                    context['video_title'] = video_title
                    # 如果没有明确指定课程ID，使用视频所属的课程ID
                    if not course_id and video_course_id:
                        course_id = video_course_id
                  # 获取视频关键词
                video_keywords = get_video_keywords(video_id, limit=20)
                video_summary = get_video_summary(video_id)
                if video_summary:
                    context['video_summary'] = video_summary
                if video_keywords:
                    context['video_keywords'] = [kw['name'] for kw in video_keywords]

            # 获取课程信息
            if course_id:
                course_name = get_course_info(course_id)
                if course_name:
                    context['course_name'] = course_name
                
                # 获取课程关键词
                course_keywords = get_course_keywords(course_id, limit=10)
                if course_keywords:
                    # 按重要性分类关键词
                    core_concepts = [kw['name'] for kw in course_keywords if kw['category'] == 'core_concept']
                    main_modules = [kw['name'] for kw in course_keywords if kw['category'] == 'main_module']
                    specific_points = [kw['name'] for kw in course_keywords if kw['category'] == 'specific_point']
                    
                    context['course_keywords'] = {
                        'core_concepts': core_concepts[:3],  # 取前3个核心概念
                        'main_modules': main_modules[:4],    # 取前4个主要模块
                        'specific_points': specific_points[:5]  # 取前5个具体知识点
                    }
                    
        except Exception as e:
            if has_app_context():
                current_app.logger.warning(f"构建上下文信息时出错: {str(e)}")
        
        return context

    def _build_video_chat_prompt(self, context_info):
        """构建视频聊天的prompt模板"""
        prompt_parts = [
            "你是一名专业的教育内容讲解助手，正在为学生解答关于特定视频内容的问题。"
        ]
        
        # 添加视频上下文信息
        if 'video_title' in context_info:
            prompt_parts.append(f"\n当前视频: {context_info['video_title']}")
        if 'video_summary' in context_info:
            prompt_parts.append(f"视频摘要: {context_info['video_summary']}")

        if 'course_name' in context_info:
            prompt_parts.append(f"所属课程: {context_info['course_name']}")
        
        if 'video_keywords' in context_info and context_info['video_keywords']:
            keywords_str = "、".join(context_info['video_keywords'])
            prompt_parts.append(f"视频关键概念: {keywords_str}")
        

        # 添加检索文档和回答指引
        prompt_parts.extend([
            "\n以下是检索到的相关教学文档:",
            "{context}",
            "\n回答指引:",
            "- 当引用上述教学片段中的信息时，请使用[数字]格式进行标注，例如\"答案XXXX[1]\"",
            "- 数字对应教学片段在上下文中的出现顺序（从1开始）",
            "- 根据视频的具体内容和关键概念来回答问题，但是不必用括号标注对于关键概念的引用",
            "- 如果问题与当前视频内容相关，请重点关注视频相关的信息",
            "- 请确保引用标注与文档顺序严格对应，不要混淆编号",
            "\n用户问题: {question}",
            "\n请基于上述文档和视频上下文信息回答问题，并正确标注引用来源："
        ])
        
        return "\n".join(prompt_parts)

    def _build_course_chat_prompt(self, context_info):
        """构建课程聊天的prompt模板"""
        prompt_parts = [
            "你是一名专业的教育内容讲解助手，正在为学生解答关于整个课程的问题。"
        ]
          # 添加课程上下文信息
        if 'course_name' in context_info:
            prompt_parts.append(f"\n当前课程: {context_info['course_name']}")
        
        if 'course_keywords' in context_info:
            course_kw = context_info['course_keywords']
            if course_kw.get('core_concepts'):
                prompt_parts.append(f"核心概念: {', '.join(course_kw['core_concepts'])}")
            if course_kw.get('main_modules'):
                prompt_parts.append(f"主要模块: {', '.join(course_kw['main_modules'])}")
            if course_kw.get('specific_points'):
                prompt_parts.append(f"重要知识点: {', '.join(course_kw['specific_points'])}")
        
        # 添加检索文档和回答指引
        prompt_parts.extend([
            "\n以下是检索到的相关教学文档:",
            "{context}",
            "\n回答指引:",
            "- 当引用上述教学片段中的信息时，请使用[数字]格式进行标注，例如\"答案XXXX[1]\"",
            "- 数字对应教学片段在上下文中的出现顺序（从1开始）",
            "- 结合课程的整体结构和知识体系来回答问题",
            "- 可以适当关联课程中的不同概念和模块",
            "- 请确保引用标注与文档顺序严格对应，不要混淆编号",
            "\n用户问题: {question}",
            "\n请基于上述文档和课程上下文信息回答问题，并正确标注引用来源："
        ])
        
        return "\n".join(prompt_parts)

    def _build_default_rag_prompt(self):
        """构建默认RAG模式的prompt模板"""
        return """你是一名教育内容讲解助手，请基于检索到的上下文回答用户的问题。

以下是检索到的相关文档：
{context}

重要提示：
- 当引用上述教学片段中的信息时，请使用[数字]格式进行标注，但是你不需要显示地说，例如"根据文档[1]，我"，而是"答案XXXX[1]"
- 数字对应教学片段在上下文中的出现顺序（从1开始）
- 例如：如果信息来自第一个出现的教学片段，使用[1]；第二个教学片段使用[2]，以此类推
- 请确保引用标注与文档顺序严格对应，不要混淆编号

问题: {question}

请基于上述文档回答问题，并正确标注引用来源："""


# 全局问答链服务实例
qa_chain_service = QAChainService()
