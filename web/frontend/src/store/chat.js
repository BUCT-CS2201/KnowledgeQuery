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
        
        // 如果使用DeepSeek模型且启用流式输出
        if (messageData.model === 'deepseek' && messageData.stream) {
          // 添加一个空的AI消息，用于流式填充
          const aiMessage = {
            id: Date.now() + 1,
            content: '',
            is_user: false,
            created_at: new Date().toISOString()
          }
          this.messages.push(aiMessage)
          
          try {
            // 先发送用户消息并获取消息ID
            const messageResponse = await axios.post(
              `/api/v1/chat/sessions/${this.currentSession.id}/messages`, 
              {
                ...messageData,
                stream: false // 先用普通方式发送用户消息
              },
              {
                headers: {
                  Authorization: `Bearer ${authStore.token}`
                }
              }
            )
            
            // 获取用户消息ID，用于后续识别会话
            const userMessageId = messageResponse.data[0].id
            console.log(`用户消息已发送，ID=${userMessageId}，开始流式接收...`)
            
            // 使用fetch API进行流式处理
            console.log('使用fetch API进行流式请求')
            const response = await fetch(
              `/api/v1/chat/sessions/${this.currentSession.id}/messages/stream`, 
              {
                method: 'GET',
                headers: {
                  'Authorization': `Bearer ${authStore.token}`,
                  'Accept': 'text/event-stream',
                  'Cache-Control': 'no-cache',
                },
                credentials: 'include'
              }
            )
            
            if (!response.ok) {
              console.error(`流式响应HTTP错误: ${response.status} ${response.statusText}`)
              throw new Error(`流式响应错误: ${response.status} ${response.statusText}`)
            }
            
            console.log('开始处理流式响应...')
            // 获取响应流
            const reader = response.body.getReader()
            const decoder = new TextDecoder('utf-8')
            let buffer = ''
            let done = false
            
            // 处理流
            while (!done) {
              const { value, done: readerDone } = await reader.read()
              if (readerDone) {
                done = true
                break
              }
              
              // 解码数据
              const text = decoder.decode(value, { stream: true })
              console.log(`收到数据块: ${text.length} 字节`)
              buffer += text
              
              // 处理完整的SSE消息
              const messages = buffer.split('\n\n')
              console.log(`拆分后得到 ${messages.length} 条消息`)
              buffer = messages.pop() || ''
              
              for (const message of messages) {
                console.log(`处理消息: ${message.substring(0, 50)}...`)
                if (message.startsWith('data: ')) {
                  let data = message.slice(6) // 移除 "data: " 前缀
                  
                  if (data === '[DONE]') {
                    console.log('收到完成信号: [DONE]')
                    done = true
                    break
                  }
                  
                  try {
                    console.log(`尝试解析JSON: ${data.substring(0, 50)}...`)
                    const parsedData = JSON.parse(data)
                    console.log("解析成功，数据:", parsedData)
                    const content = parsedData.choices?.[0]?.delta?.content || ''
                    
                    if (content) {
                      console.log(`收到内容: ${content}`)
                      // 更新AI消息内容
                      const aiMessageIndex = this.messages.findIndex(m => m.id === aiMessage.id)
                      if (aiMessageIndex !== -1) {
                        console.log(`更新消息索引 ${aiMessageIndex}`)
                        this.messages[aiMessageIndex].content += content
                        // 强制更新视图（虽然Vue应该自动做这个，但为了安全起见）
                        this.messages = [...this.messages]
                        console.log(`更新后的消息内容: ${this.messages[aiMessageIndex].content.length} 字符`)
                      } else {
                        console.warn(`未找到AI消息ID ${aiMessage.id}`)
                      }
                    } else {
                      console.log("解析的内容为空")
                    }
                  } catch (error) {
                    console.error('解析流式消息失败:', error, data)
                  }
                }
              }
            }
            
            console.log('流式连接已关闭')
            this.loading = false
          } catch (error) {
            console.error('流式请求失败:', error)
            this.error = '接收流式回复失败，请重试'
            this.loading = false
            
            // 添加错误信息到AI消息
            const aiMessageIndex = this.messages.findIndex(m => m.id === aiMessage.id)
            if (aiMessageIndex !== -1) {
              this.messages[aiMessageIndex].content = '流式响应出错，请重试。'
            }
          }
          
          // 更新会话列表中的时间
          const sessionIndex = this.sessions.findIndex(s => s.id === this.currentSession.id)
          if (sessionIndex !== -1) {
            this.sessions[sessionIndex].updated_at = new Date().toISOString()
            this.sessions.sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
          }
          
          // 如果是第一条消息，更新会话标题
          if (this.messages.length <= 3 && this.currentSession.title === '新对话') {
            // 从用户消息生成标题
            let title = messageData.content
            // 如果消息太长，截取前20个字符
            if (title.length > 20) {
              title = title.substring(0, 20) + '...'
            }
            this.updateSessionTitle(`关于 ${title} 的对话`)
          }
          
          return true
        }
        
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
        if (!messageData.model === 'deepseek' || !messageData.stream) {
          this.loading = false
        }
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