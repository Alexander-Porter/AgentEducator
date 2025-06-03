import apiClient from './index';

export default {
  // 获取视频列表
  getVideos(params) {
    return apiClient.get('/api/videos', { params });
  },

  // 获取视频详情
  getVideoDetail(videoId) {
    return apiClient.get(`/api/videos/${videoId}`);
  },

  // 上传视频
  uploadVideo(formData, config = {}) {
    return apiClient.post('/api/uploads/course_video', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      ...config
    });
  },

  // 更新视频信息
  updateVideo(videoId, data) {
    return apiClient.put(`/api/videos/${videoId}`, data);
  },

  // 删除视频 - 已使用DELETE方法
  deleteVideo(videoId) {
    return apiClient.delete(`/api/videos/${videoId}`);
  },

  // 搜索视频
  searchVideos(params) {
    return apiClient.get('/api/videos/search', { params });
  },

  // 更新视频观看进度
  updateProgress(videoId, data) {
    return apiClient.post(`/api/videos/${videoId}/progress`, data);
  },

  // 获取视频评论列表
  getVideoComments(videoId, params = {}) {
    return apiClient.get(`/api/videos/${videoId}/comments`, { params });
  },

  // 添加视频评论
  addVideoComment(videoId, data) {
    return apiClient.post(`/api/videos/${videoId}/comments`, data);
  },

  // 点赞/取消点赞评论
  likeComment(commentId, data) {
    return apiClient.post(`/api/videos/comments/${commentId}/like`, data);
  },
  
  // 处理视频 - 触发视频分析处理任务
  processVideo(videoId) {
    return apiClient.post(`/api/videos/${videoId}/process`);
  },

  // 删除评论
  deleteComment(commentId) {
    return apiClient.delete(`/api/videos/comments/${commentId}`);
  }
};
