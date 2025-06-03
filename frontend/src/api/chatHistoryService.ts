import apiClient from './index';

// 接口定义
export interface ChatMessage {
  id: string;
  session_id: string;
  role: string;
  content: string;
  time_references?: any[];
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  video_id?: string;
  course_id?: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  type: 'general' | 'video' | 'course';
  video_info?: {
    id: string;
    title: string;
    cover_url: string;
  };
  course_info?: {
    id: string;
    name: string;
    code: string;
  };
}

export default {
  // 获取聊天会话列表
  getChatSessionsList(params: { page?: number; size?: number; videoId?: string; courseId?: string; includeAll?: boolean } = {}) {
    return apiClient.get('/api/chat_history/list', { params });
  },
  
  // 获取聊天会话详情
  getChatSessionDetail(sessionId: string) {
    return apiClient.get(`/api/chat_history/detail/${sessionId}`);
  },
  
  // 创建新的聊天会话
  createChatSession(data: { title?: string, videoId?: string, courseId?: string }) {
    return apiClient.post('/api/chat_history/create', data);
  },
  
  // 更新聊天会话
  updateChatSession(sessionId: string, data: { title: string }) {
    return apiClient.put(`/api/chat_history/update/${sessionId}`, data);
  },
  
  // 删除聊天会话
  deleteChatSession(sessionId: string) {
    return apiClient.delete(`/api/chat_history/delete/${sessionId}`);
  }
}; 