"""回调处理器模块"""
import json
from langchain_core.callbacks import BaseCallbackHandler


class StreamingCallback(BaseCallbackHandler):
    """优化的流式回调处理器"""
    
    def __init__(self, queue):
        self.queue = queue
        self.token_count = 0

    def on_llm_new_token(self, token, **kwargs):
        """当LLM生成新token时被调用"""
        self.token_count += 1
        self.queue.put(token)


class OptimizedStreamingCallback(BaseCallbackHandler):
    """通用模式优化的流式回调处理器"""
    
    def __init__(self, queue):
        self.queue = queue
        self.token_count = 0
        self.answer_content = ""
        self.token_buffer = ""  # 用于缓冲token以处理Markdown序号
        
    def on_llm_new_token(self, token, **kwargs):
        self.answer_content += token
        self.token_count += 1
        
        # 使用智能缓冲机制处理Markdown序号
        self._process_token_with_buffer(token)
    
    def _process_token_with_buffer(self, token):
        """智能缓冲处理token，确保Markdown序号不被分割"""
        self.token_buffer += token
        
        # 检查是否可以释放缓冲区的内容
        if self._should_flush_buffer():
            # 释放整个缓冲区
            self.queue.put(self.token_buffer)
            self.token_buffer = ""
        elif len(self.token_buffer) > 50:  # 防止缓冲区过大
            # 如果缓冲区太大，释放前面的内容，保留可能的序号部分
            if self._contains_potential_number_marker():
                # 找到最后一个数字的位置，保留从那里开始的内容
                last_digit_pos = -1
                for i in range(len(self.token_buffer) - 1, -1, -1):
                    if self.token_buffer[i].isdigit():
                        last_digit_pos = i
                        break
                
                if last_digit_pos > 10:  # 确保不会保留太多
                    self.queue.put(self.token_buffer[:last_digit_pos])
                    self.token_buffer = self.token_buffer[last_digit_pos:]
                else:
                    self.queue.put(self.token_buffer[:-10])
                    self.token_buffer = self.token_buffer[-10:]
            else:
                self.queue.put(self.token_buffer)
                self.token_buffer = ""
    
    def _should_flush_buffer(self):
        """判断是否应该释放缓冲区"""
        if not self.token_buffer:
            return False
            
        # 如果缓冲区不包含潜在的序号标记，可以直接释放
        if not self._contains_potential_number_marker():
            return True
            
        # 检查是否已经形成完整的序号标记
        import re
        # 匹配各种序号格式：1. 、1）、1) 等
        complete_marker_pattern = r'^\d+[.）)]\s*\*{0,2}'
        if re.search(complete_marker_pattern, self.token_buffer):
            # 检查后面是否还有更多内容，如果有则可以释放
            marker_match = re.search(complete_marker_pattern, self.token_buffer)
            if marker_match and len(self.token_buffer) > marker_match.end():
                return True
        
        # 如果以句号、感叹号、问号等结尾，可以释放
        if re.search(r'[.!?。！？]\s*$', self.token_buffer):
            return True
            
        # 如果以换行符结尾，可以释放
        if self.token_buffer.endswith('\n'):
            return True
            
        return False
    
    def _contains_potential_number_marker(self):
        """检查缓冲区是否包含潜在的序号标记"""
        import re
        # 检查是否包含数字后跟可能的序号标记
        return bool(re.search(r'\d+[.）)]*\s*\*{0,2}$', self.token_buffer))
    
    def flush_remaining_buffer(self):
        """强制释放剩余的缓冲区内容（在流结束时调用）"""
        if self.token_buffer:
            self.queue.put(self.token_buffer)
            self.token_buffer = ""


class CustomStreamingCallback(BaseCallbackHandler):
    """RAG模式自定义流式回调处理器"""
    
    def __init__(self, queue):
        self.queue = queue
        self.token_count = 0
        self.answer_content = ""
        self.token_buffer = ""  # 用于缓冲token以处理Markdown序号
        
    def on_llm_new_token(self, token, **kwargs):
        self.answer_content += token
        self.token_count += 1
        
        # 使用智能缓冲机制处理Markdown序号
        self._process_token_with_buffer(token)
    
    def _process_token_with_buffer(self, token):
        """智能缓冲处理token，确保Markdown序号不被分割"""
        self.token_buffer += token
        
        # 检查是否可以释放缓冲区的内容
        if self._should_flush_buffer():
            # 释放整个缓冲区
            self.queue.put(self.token_buffer)
            self.token_buffer = ""
        elif len(self.token_buffer) > 50:  # 防止缓冲区过大
            # 如果缓冲区太大，释放前面的内容，保留可能的序号部分
            if self._contains_potential_number_marker():
                # 找到最后一个数字的位置，保留从那里开始的内容
                last_digit_pos = -1
                for i in range(len(self.token_buffer) - 1, -1, -1):
                    if self.token_buffer[i].isdigit():
                        last_digit_pos = i
                        break
                
                if last_digit_pos > 10:  # 确保不会保留太多
                    self.queue.put(self.token_buffer[:last_digit_pos])
                    self.token_buffer = self.token_buffer[last_digit_pos:]
                else:
                    self.queue.put(self.token_buffer[:-10])
                    self.token_buffer = self.token_buffer[-10:]
            else:
                self.queue.put(self.token_buffer)
                self.token_buffer = ""
    
    def _should_flush_buffer(self):
        """判断是否应该释放缓冲区"""
        if not self.token_buffer:
            return False
            
        # 如果缓冲区不包含潜在的序号标记，可以直接释放
        if not self._contains_potential_number_marker():
            return True
            
        # 检查是否已经形成完整的序号标记
        import re
        # 匹配各种序号格式：1. 、1）、1) 等
        complete_marker_pattern = r'^\d+[.）)]\s*\*{0,2}'
        if re.search(complete_marker_pattern, self.token_buffer):
            # 检查后面是否还有更多内容，如果有则可以释放
            marker_match = re.search(complete_marker_pattern, self.token_buffer)
            if marker_match and len(self.token_buffer) > marker_match.end():
                return True
        
        # 如果以句号、感叹号、问号等结尾，可以释放
        if re.search(r'[.!?。！？]\s*$', self.token_buffer):
            return True
            
        # 如果以换行符结尾，可以释放
        if self.token_buffer.endswith('\n'):
            return True
            
        return False
    
    def _contains_potential_number_marker(self):
        """检查缓冲区是否包含潜在的序号标记"""
        import re
        # 检查是否包含数字后跟可能的序号标记
        return bool(re.search(r'\d+[.）)]*\s*\*{0,2}$', self.token_buffer))
    
    def flush_remaining_buffer(self):
        """强制释放剩余的缓冲区内容（在流结束时调用）"""
        if self.token_buffer:
            self.queue.put(self.token_buffer)
            self.token_buffer = ""


class StatusNotifier:
    """状态通知器，用于发送处理状态消息"""
    
    def __init__(self, queue):
        self.queue = queue
    
    def notify_analysis_start(self):
        """通知分析开始"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "analysis_start", 
            "message": "分析问题中..."
        }))
    
    def notify_generation_start(self):
        """通知生成开始"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "generation_start",
            "message": "开始生成回答..."
        }))
    
    def notify_retrieval_start(self):
        """通知检索开始"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "retrieval_start",
            "message": "检索相关资料..."
        }))
    
    def notify_retrieval_complete(self, doc_count=0):
        """通知检索完成"""
        index_info = f"已加载 {doc_count} 个文档片段" if doc_count > 0 else ""
        self.queue.put(json.dumps({
            "type": "status", 
            "stage": "retrieval_complete",
            "message": f"检索完成 {index_info}",
            "stats": {"document_count": doc_count}
        }))
    
    def notify_question_analysis(self):
        """通知问题分析"""
        self.queue.put(json.dumps({
            "type": "status",
            "stage": "question_analysis", 
            "message": "思考中..."
        }))
