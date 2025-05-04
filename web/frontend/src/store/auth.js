import { defineStore } from 'pinia'
import axios from 'axios'
import router from '../router'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    loading: false,
    error: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token,
    getUser: (state) => state.user,
    getLoading: (state) => state.loading,
    getError: (state) => state.error
  },
  
  actions: {
    // 登录
    async login(username, password) {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.post('/api/v1/auth/json-login', {
          username,
          password
        })
        
        const { access_token, token_type } = response.data
        this.token = access_token
        localStorage.setItem('token', access_token)
        
        // 获取用户信息
        await this.fetchUserProfile()
        
        router.push('/')
      } catch (error) {
        this.error = error.response?.data?.detail || '登录失败，请检查用户名和密码'
        console.error('Login error:', error)
      } finally {
        this.loading = false
      }
    },
    
    // 注册
    async register(username, email, password) {
      this.loading = true
      this.error = null
      
      try {
        await axios.post('/api/v1/auth/register', {
          username,
          email,
          password
        })
        
        // 注册成功后直接登录
        await this.login(username, password)
      } catch (error) {
        this.error = error.response?.data?.detail || '注册失败，请稍后再试'
        console.error('Register error:', error)
      } finally {
        this.loading = false
      }
    },
    
    // 获取用户资料
    async fetchUserProfile() {
      if (!this.token) return
      
      try {
        // 添加认证头
        const config = {
          headers: {
            Authorization: `Bearer ${this.token}`
          }
        }
        
        const response = await axios.get('/api/v1/auth/me', config)
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      } catch (error) {
        console.error('获取用户资料失败:', error)
        if (error.response?.status === 401) {
          this.logout()
        }
      }
    },
    
    // 登出
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // 清空聊天状态
      const { useChatStore } = require('./chat')
      const chatStore = useChatStore()
      chatStore.clearChatState()
      
      router.push('/login')
    }
  }
}) 