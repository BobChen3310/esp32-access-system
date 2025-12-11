import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'your-api-url',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Token 失效或過期，強制登出...");
      
      // 清除 LocalStorage
      localStorage.removeItem('access_token');
      
      // 強制跳轉回登入頁
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
