import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  withCredentials: true
});

// 添加请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('wendao_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // 处理 401 未授权错误
      if (error.response.status === 401) {
        localStorage.removeItem('wendao_token');
        localStorage.removeItem('wendao_user_id');
        localStorage.removeItem('wendao_user_name');
        localStorage.removeItem('wendao_user_role');
        window.location.href = '/login';
      }
      // 处理 CORS 错误
      if (error.response.status === 0 || error.code === 'ERR_NETWORK') {
        console.error('CORS或网络错误:', error);
        return Promise.reject(new Error('服务器连接失败，请检查网络连接'));
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
