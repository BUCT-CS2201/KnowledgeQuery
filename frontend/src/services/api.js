import axios from 'axios';

const API_BASE_URL = 'http://localhost:9988/v1/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 请求拦截器，添加token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 账号相关API
export const accountApi = {
  // 用户注册
  register: (userData) => {
    return api.post('/account/register', userData);
  },
  
  // 用户登录
  login: (loginData) => {
    return api.post('/account/login', loginData);
  },
  
  // 获取当前用户信息
  getCurrentUser: () => {
    return api.get('/account/me');
  }
};

// 问答相关API
export const chatApi = {
  // 发送问题
  sendQuestion: (question) => {
    return api.post('/chat/', { question });
  }
};

export default api;
