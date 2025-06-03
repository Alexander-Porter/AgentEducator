import apiClient from './index';

/*interface ChatMessage {
  role: 'user' | 'ai';
  content: string;
  timestamp: Date;
  sources?: any[];
}

interface ChatSession {
  id: string;
  title?: string;
  created_at: string;
  messages: ChatMessage[];
}
  */

// 接口定义
interface AskQuestionData {
  query: string;
  videoId?: string;
  courseId?: string;
  sessionId?: string;
  isNewSession?: boolean;
  askCourse?: boolean;
  askAllCourse?: boolean;
  history?: any[];
}

export default {
  // 常规问答请求
  askQuestion(data: any) {
    return apiClient.post('/api/qa/ask', data);
  },
  
  // 流式问答请求 - POST，支持多轮历史
  askQuestionStream({ query, videoId, courseId, sessionId, isNewSession, askCourse, askAllCourse, history }: AskQuestionData) {
    const body = {
      query,
      videoId,
      courseId,
      sessionId,
      isNewSession,
      askCourse,
      askAllCourse,
      history
    };
    return fetch(`${apiClient.defaults.baseURL}/api/qa/ask-stream`, {
      method: 'POST',
      headers: {
        'Accept': 'text/event-stream',
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('wendao_token')}`
      },
      body: JSON.stringify(body)
    });
  },
  
  // 获取视频处理状态
  checkProcessingStatus(videoId: string) {
    return apiClient.get(`/api/videos/${videoId}/processing-status`);
  },
  
  // 获取视频摘要
  getVideoSummary(videoId: string) {
    return apiClient.get(`/api/summaries/video/${videoId}`);
  },
  
  // 生成视频摘要
  generateSummary(data: any) {
    return apiClient.post('/api/summaries/generate', data);
  },
/*
  // 获取历史对话列表
  getChatHistoryList(): Promise<{ history: ChatSession[] }> {
    return apiClient.get('/api/qa/sessions');
  },

  // 获取历史对话内容
  getChatHistory(sessionId: string): Promise<ChatSession> {
    return apiClient.get(`/api/qa/sessions/${sessionId}/messages`);
  }
    */
};
