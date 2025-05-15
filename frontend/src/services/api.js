import axios from 'axios';


// const API_BASE_URL = 'http://localhost:9988/v1/api';

const API_BASE_URL = import.meta.env.VITE_APP_BASE_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
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

// 添加响应拦截器，处理401错误
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 检查是否为401未授权错误
    if (error.response && error.response.status === 401) {
      // 清除失效的token和用户信息
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // 获取当前页面URL，排除登录和注册页面（避免无限重定向）
      const currentPath = window.location.pathname;
      if (currentPath !== '/login' && currentPath !== '/register') {
        // 提示用户
        // 使用setTimeout避免在重定向前无法看到提示
        setTimeout(() => {
          alert('您的登录已过期，请重新登录');
          // 跳转到登录页面
          window.location.href = '/login';
        }, 100);
      }
    }
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
  },
  
  // 检查用户是否存在（找回密码用）
  checkUserExist: (data) => {
    return api.post('/account/check_user', data)
  },
  
  // 重置密码
  resetPassword: (data) => {
    return api.post('/account/reset_password', data)
  },
};

// 聊天相关API
export const chatApi = {
  // 发送问题（旧方法，保留兼容性）
  sendQuestion: (question) => {
    return api.post('/chat/', { question });
  },
  
  // 创建新聊天会话
  createSession: (title = "新对话", type = 1) => {
    return api.post('/chat/sessions', { title, type });
  },
  
  // 获取用户的所有聊天会话
  getSessions: () => {
    return api.get('/chat/sessions');
  },
  
  // 获取单个聊天会话及其消息
  getSession: (sessionId) => {
    return api.get(`/chat/sessions/${sessionId}`);
  },

  // 发送消息并获取AI回复
  sendMessage: (sessionId, content) => {
    return api.post(`/chat/sessions/${sessionId}/messages`, { content });
  },
  
  // 发送消息并获取AI流式回复
  sendStreamMessage: (sessionId, content, model = '') => {
    const token = localStorage.getItem('token');
    return {
      url: `${API_BASE_URL}/chat/sessions/${sessionId}/stream`,
      options: {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : '',
          'Cache-Control': 'no-cache',
          'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({ content, model }),
        // 确保使用正确的模式处理流
        cache: 'no-store',
        credentials: 'same-origin'
      }
    };
  },
  
  // 根据会话类型创建会话的简便方法
  createNormalSession: (title = "新对话") => {
    return api.post('/chat/sessions', { title, type: 1 });
  },
  
  createKnowledgeBaseSession: (title = "新知识库问答") => {
    return api.post('/chat/sessions', { title, type: 2 });
  },
  
  createKnowledgeGraphSession: (title = "新知识图谱问答") => {
    return api.post('/chat/sessions', { title, type: 3 });
  },
    
  // 删除聊天会话
  deleteSession: (sessionId) => {
    return api.delete(`/chat/sessions/${sessionId}`);
  },
  
  // 更新聊天会话标题
  updateSession: (sessionId, title) => {
    return api.put(`/chat/sessions/${sessionId}`, { title });
  },
};

export default api;
