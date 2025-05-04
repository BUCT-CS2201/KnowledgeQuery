import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './auth'
import { ElMessage } from 'element-plus'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    currentSession: null,
    messages: [],
    loading: false,
    error: null
  }),
  
  getters: {
    getSessions: (state) => state.sessions,
    getCurrentSession: (state) => state.currentSession,
    getMessages: (state) => state.messages,
    getLoading: (state) => state.loading,
    getError: (state) => state.error
  },
  
  actions: {
    // 获取用户所有聊天会话
    async fetchSessions() {
      this.loading = true
      this.error = null
      
      try {
        const authStore = useAuthStore()
        const config = {
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
        
        const response = await axios.get('/api/v1/chat/sessions', config)
        this.sessions = response.data
      } catch (error) {
        this.error = error.response?.data?.detail || '获取聊天列表失败'
        console.error('Fetch sessions error:', error)
        ElMessage.error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    // 创建新的聊天会话
    async createSession(title = '新对话') {
      this.loading = true
      this.error = null
      
      try {
        const authStore = useAuthStore()
        const config = {
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
        
        const response = await axios.post('/api/v1/chat/sessions', { title }, config)
        const newSession = response.data
        
        this.sessions.unshift(newSession) // 添加到列表开头
        this.selectSession(newSession.id)
        
        return newSession
      } catch (error) {
        this.error = error.response?.data?.detail || '创建对话失败'
        console.error('Create session error:', error)
        ElMessage.error(this.error)
        return null
      } finally {
        this.loading = false
      }
    },
    
    // 选择当前会话
    async selectSession(sessionId) {
      this.loading = true
      this.error = null
      
      try {
        const authStore = useAuthStore()
        const config = {
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
        
        const response = await axios.get(`/api/v1/chat/sessions/${sessionId}`, config)
        this.currentSession = response.data
        this.messages = response.data.messages
      } catch (error) {
        this.error = error.response?.data?.detail || '获取聊天记录失败'
        console.error('Select session error:', error)
        ElMessage.error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    // 发送消息
    async sendMessage(messageData) {
      if (!this.currentSession) return
      
      this.loading = true
      this.error = null
      
      try {
        const authStore = useAuthStore()
        const config = {
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
        
        // 先添加用户消息到UI
        const userMessage = {
          id: Date.now(),
          content: messageData.content,
          is_user: true,
          created_at: new Date().toISOString(),
          files: messageData.files
        }
        this.messages.push(userMessage)
        
        // 非流式处理方式
        const response = await axios.post(
          `/api/v1/chat/sessions/${this.currentSession.id}/messages`, 
          messageData, 
          config
        )
        
        // 更新本地用户消息ID，并添加系统回复
        if (response.data.length > 1) {
          // 第一个是用户消息，第二个是系统回复
          const [serverUserMsg, systemReply] = response.data
          
          // 更新本地用户消息的ID
          const userMessageIndex = this.messages.findIndex(m => m.id === userMessage.id)
          if (userMessageIndex !== -1) {
            this.messages[userMessageIndex].id = serverUserMsg.id
          }
          
          // 添加系统回复
          this.messages.push({
            ...systemReply,
          })
          
          // 如果是第一条消息，更新会话标题
          if (this.messages.length <= 2 && this.currentSession.title === '新对话') {
            // 从用户消息生成标题
            let title = messageData.content
            // 如果消息太长，截取前20个字符
            if (title.length > 20) {
              title = title.substring(0, 20) + '...'
            }
            this.updateSessionTitle(`关于 ${title} 的对话`)
          }
        }
        
        // 更新会话列表中的时间
        const sessionIndex = this.sessions.findIndex(s => s.id === this.currentSession.id)
        if (sessionIndex !== -1) {
          this.sessions[sessionIndex].updated_at = new Date().toISOString()
          this.sessions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
        }
        
        return true
      } catch (error) {
        console.error('发送消息失败:', error)
        this.error = '发送消息失败，请重试'
        return false
      } finally {
        this.loading = false
      }
    },
    
    // 发送带文件的消息
    async sendMessageWithFiles(messageData, files) {
      if (!this.currentSession) return
      
      this.loading = true
      this.error = null
      
      try {
        const authStore = useAuthStore()
        const config = {
          headers: {
            Authorization: `Bearer ${authStore.token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
        
        // 先添加用户消息到UI
        const userMessage = {
          id: Date.now(),
          content: messageData.content,
          is_user: true,
          created_at: new Date().toISOString(),
          files: files.map(f => ({
            name: f.name,
            size: f.size,
            type: f.type
          }))
        }
        this.messages.push(userMessage)
        
        // 准备表单数据
        const formData = new FormData()
        formData.append('content', messageData.content)
        formData.append('model', messageData.model)
        formData.append('web_search', messageData.web_search)
        
        // 添加文件
        files.forEach(file => {
          formData.append('files', file)
        })
        
        // 发送消息到服务器
        const response = await axios.post(
          `/api/v1/chat/sessions/${this.currentSession.id}/messages/with-files`,
          formData,
          config
        )
        
        // 更新本地用户消息ID，并添加系统回复
        if (response.data.length > 1) {
          // 第一个是用户消息，第二个是系统回复
          const [serverUserMsg, systemReply] = response.data
          
          // 更新本地用户消息的ID
          const userMessageIndex = this.messages.findIndex(m => m.id === userMessage.id)
          if (userMessageIndex !== -1) {
            this.messages[userMessageIndex].id = serverUserMsg.id
          }
          
          // 添加系统回复
          this.messages.push({
            ...systemReply
          })
          
          // 如果是第一条消息，更新会话标题
          if (this.currentSession.title === '新对话') {
            const fileName = files[0].name
            this.updateSessionTitle(`关于 ${fileName} 的对话`)
          }
        }
        
        // 更新会话列表中的时间
        const sessionIndex = this.sessions.findIndex(s => s.id === this.currentSession.id)
        if (sessionIndex !== -1) {
          this.sessions[sessionIndex].updated_at = new Date().toISOString()
          this.sessions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
        }
        
        return true
      } catch (error) {
        console.error('发送消息失败:', error)
        this.error = '发送消息失败，请重试'
        return false
      } finally {
        this.loading = false
      }
    },
    
    // 更新会话标题
    async updateSessionTitle(title) {
      if (!this.currentSession) return
      
      try {
        const authStore = useAuthStore()
        const config = {
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
        
        const response = await axios.put(
          `/api/v1/chat/sessions/${this.currentSession.id}`, 
          { title }, 
          config
        )
        
        // 更新当前会话标题
        this.currentSession.title = title
        
        // 更新会话列表中的标题
        const sessionIndex = this.sessions.findIndex(s => s.id === this.currentSession.id)
        if (sessionIndex !== -1) {
          this.sessions[sessionIndex].title = title
        }
        
        return response.data
      } catch (error) {
        console.error('Update session title error:', error)
        ElMessage.error('更新会话标题失败')
        return null
      }
    },
    
    // 删除会话
    async deleteSession(sessionId) {
      this.loading = true
      this.error = null
      
      try {
        const authStore = useAuthStore()
        const config = {
          headers: {
            Authorization: `Bearer ${authStore.token}`
          }
        }
        
        await axios.delete(`/api/v1/chat/sessions/${sessionId}`, config)
        
        // 从列表中删除会话
        this.sessions = this.sessions.filter(s => s.id !== sessionId)
        
        // 如果删除的是当前会话，清空当前会话
        if (this.currentSession && this.currentSession.id === sessionId) {
          this.currentSession = null
          this.messages = []
          
          // 如果还有其他会话，选择第一个
          if (this.sessions.length > 0) {
            this.selectSession(this.sessions[0].id)
          }
        }
      } catch (error) {
        this.error = error.response?.data?.detail || '删除会话失败'
        console.error('Delete session error:', error)
        ElMessage.error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    // 清空聊天状态（退出登录时调用）
    clearChatState() {
      this.sessions = []
      this.currentSession = null
      this.messages = []
      this.loading = false
      this.error = null
    },
    
    // 格式化文件大小（内部辅助方法）
    _formatFileSize(size) {
      if (size < 1024) {
        return size + ' B'
      } else if (size < 1024 * 1024) {
        return (size / 1024).toFixed(2) + ' KB'
      } else if (size < 1024 * 1024 * 1024) {
        return (size / (1024 * 1024)).toFixed(2) + ' MB'
      } else {
        return (size / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
      }
    }
  }
}) 