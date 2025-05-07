<template>
  <div class="web-container">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <h1>✨ 知识问答系统</h1>
      </div>
      <div class="sidebar-content">
        <el-menu :default-active="activeMenu" class="sidebar-menu" :collapse="sidebarCollapsed">
          <el-menu-item index="chat" @click="activateChat">
            <el-icon><ChatDotSquare /></el-icon>
            <span>💬 问答系统</span>
          </el-menu-item>
          
          <!-- 历史会话直接展示 -->
          <div class="history-section">
            <div class="history-header">
              <span>📚 历史会话</span>
              <el-button 
                type="text" 
                class="new-session-btn"
                @click="createNewSession"
              >
                <el-icon><Plus /></el-icon>
              </el-button>
            </div>
            
            <div class="session-list">
              <div
                v-for="session in chatSessions"
                :key="session.id"
                :class="['session-item', currentSessionId === session.id ? 'active' : '']"
                @click="switchSession(session.id)"
              >
                <el-icon><ChatLineRound /></el-icon>
                <span class="session-title">{{ session.title }}</span>
                <div class="session-actions">
                  <el-dropdown trigger="click" @click.stop>
                    <el-icon><MoreFilled /></el-icon>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click.stop="renameSession(session)">
                          <el-icon><Edit /></el-icon> 重命名
                        </el-dropdown-item>
                        <el-dropdown-item @click.stop="deleteSession(session.id)">
                          <el-icon><Delete /></el-icon> 删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
              <div v-if="chatSessions.length === 0" class="no-sessions">
                暂无会话历史
              </div>
            </div>
          </div>
        </el-menu>
      </div>
      <div class="sidebar-footer">
        <div class="user-panel">
          <span class="user-emoji">👤</span>
          <div class="user-info">
            <div class="username">{{ user?.name || '未登录' }}</div>
            <el-dropdown trigger="click">
              <span class="user-status">
                <span class="status-dot"></span> 在线
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 侧边栏伸缩按钮 -->
    <div class="sidebar-toggle" @click="toggleSidebar">
      <el-icon v-if="sidebarCollapsed"><ArrowRight /></el-icon>
      <el-icon v-else><ArrowLeft /></el-icon>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content" :class="{ 'content-expanded': sidebarCollapsed }">
      <!-- 聊天区域 -->
      <div class="chat-content custom-scrollbar" ref="chatContentRef">
        <div v-if="chatMessages.length === 0" class="welcome">
          <div class="welcome-container">
            <div class="welcome-header">
              <h2>🤖 欢迎使用博物馆知识问答系统</h2>
              <p>有任何关于博物馆的问题，尽管问我吧！</p>
            </div>
            
            <!-- 中间大型搜索框 -->
            <div class="center-search">
              <el-input
                v-model="userInput"
                placeholder="请输入您想了解的博物馆知识..."
                :disabled="loading"
                type="textarea"
                :rows="3"
                resize="none"
                @keyup.enter.ctrl.prevent="sendMessage"
                ref="centerInputRef"
                class="welcome-input"
              />
              <el-button
                type="primary"
                size="large"
                :disabled="loading || !userInput.trim()"
                @click="sendMessage"
                class="welcome-button"
              >
                开始提问 <el-icon class="el-icon--right"><Position /></el-icon>
              </el-button>
            </div>
            
            <div class="quick-examples">
              <h3>💡 示例问题</h3>
              <div class="examples-list">
                <div class="example-item" @click="useExample('故宫的历史是怎样的？')">
                  🏛️ 故宫的历史是怎样的？
                </div>
                <div class="example-item" @click="useExample('中国古代青铜器有哪些特点？')">
                  🥉 中国古代青铜器有哪些特点？
                </div>
                <div class="example-item" @click="useExample('敦煌莫高窟有哪些著名壁画？')">
                  🖼️ 敦煌莫高窟有哪些著名壁画？
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="message-list">
          <div
            v-for="(message, index) in chatMessages"
            :key="index"
            :class="['message', message.type === 'user' ? 'user-message' : 'ai-message']"
          >
            <!-- AI消息 -->
            <template v-if="message.type !== 'user'">
              <div class="message-emoji">🤖</div>
              <div class="message-content ai-content">
                <div class="message-text markdown-body" v-html="renderMarkdown(message.content)"></div>
              </div>
            </template>
            
            <!-- 用户消息 -->
            <template v-else>
              <div class="user-message-emoji">😊</div>
              <div class="message-content user-content">
                <div class="message-text">{{ message.content }}</div>
              </div>
            </template>
          </div>
        </div>

        <div v-if="loading" class="loading-indicator">
          <el-skeleton :rows="2" animated />
        </div>
      </div>

      <!-- 输入区域 - 只在有消息时显示 -->
      <div class="chat-input-area" v-if="chatMessages.length > 0">
        <el-input
          v-model="userInput"
          placeholder="请输入您想了解的博物馆知识..."
          :disabled="loading"
          type="textarea"
          :rows="2"
          resize="none"
          @keyup.enter.ctrl.prevent="sendMessage"
          ref="inputRef"
        />
        <div class="input-actions">
          <el-button
            type="primary"
            :disabled="loading || !userInput.trim()"
            @click="sendMessage"
          >
            发送 <el-icon class="el-icon--right"><Position /></el-icon>
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 会话重命名对话框 -->
    <el-dialog
      v-model="renameDialogVisible"
      title="重命名会话"
      width="30%"
      :close-on-click-modal="false"
    >
      <el-input v-model="newSessionTitle" placeholder="请输入新的会话名称" />
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="renameDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmRenameSession">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { chatApi } from '../services/api'
import MarkdownIt from 'markdown-it'
import { 
  ChatDotSquare, 
  DocumentCopy, 
  Position,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Service,
  ChatLineRound,
  Edit,
  Delete,
  Plus,
  MoreFilled
} from '@element-plus/icons-vue'

// 初始化markdown-it解析器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str, lang) {
    // 这里可以添加代码高亮插件，例如highlight.js或prismjs
    return `<pre class="language-${lang}"><code>${str}</code></pre>`;
  }
});

const router = useRouter()
const loading = ref(false)
const userInput = ref('')
const chatContentRef = ref(null)
const inputRef = ref(null)
const centerInputRef = ref(null)
const chatMessages = reactive([])
const currentSessionId = ref(null)
const chatSessions = ref([])
const activeMenu = ref('chat')
const renameDialogVisible = ref(false)
const newSessionTitle = ref('')
const sessionToRename = ref(null)
// 侧边栏折叠状态
const sidebarCollapsed = ref(false)

// 切换侧边栏的展开/折叠状态
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 从本地存储获取用户信息
const user = computed(() => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
})

// 激活聊天页面
const activateChat = () => {
  activeMenu.value = 'chat'
}

// 加载所有聊天会话
const loadChatSessions = async () => {
  try {
    const response = await chatApi.getSessions()
    if (response.data && response.data.data) {
      chatSessions.value = response.data.data
    }
  } catch (error) {
    console.error('获取聊天会话列表失败:', error)
    ElMessage.error('获取会话列表失败')
  }
}

// 切换聊天会话
const switchSession = async (sessionId) => {
  if (currentSessionId.value === sessionId) return
  
  try {
    loading.value = true
    const response = await chatApi.getSession(sessionId)
    
    if (response.data && response.data.data) {
      const sessionData = response.data.data
      
      // 更新当前会话ID
      currentSessionId.value = sessionId
      
      // 清空并更新消息列表
      chatMessages.length = 0
      
      if (sessionData.messages && sessionData.messages.length > 0) {
        sessionData.messages.forEach(msg => {
          chatMessages.push({
            type: msg.is_user ? 'user' : 'system',
            content: msg.content
          })
        })
      }
      
      // 滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
    }
  } catch (error) {
    console.error('加载会话消息失败:', error)
    ElMessage.error('加载会话消息失败')
  } finally {
    loading.value = false
  }
}

// 创建新会话
const createNewSession = async () => {
  try {
    const response = await chatApi.createSession('新对话')
    if (response.data && response.data.data) {
      const newSession = response.data.data
      
      // 添加到会话列表
      chatSessions.value.unshift({
        id: newSession.id,
        title: newSession.title,
        created_at: newSession.created_at
      })
      
      // 切换到新会话
      currentSessionId.value = newSession.id
      chatMessages.length = 0
      
      ElMessage.success('创建会话成功')
    }
  } catch (error) {
    console.error('创建会话失败:', error)
    ElMessage.error('创建会话失败')
  }
}

// 删除会话
const deleteSession = (sessionId) => {
  ElMessageBox.confirm('确定要删除这个会话吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await chatApi.deleteSession(sessionId)
      
      // 从列表中移除
      chatSessions.value = chatSessions.value.filter(s => s.id !== sessionId)
      
      // 如果删除的是当前会话，则清空消息
      if (currentSessionId.value === sessionId) {
        currentSessionId.value = null
        chatMessages.length = 0
      }
      
      ElMessage.success('删除会话成功')
    } catch (error) {
      console.error('删除会话失败:', error)
      ElMessage.error('删除会话失败')
    }
  }).catch(() => {})
}

// 打开重命名对话框
const renameSession = (session) => {
  sessionToRename.value = session
  newSessionTitle.value = session.title
  renameDialogVisible.value = true
}

// 确认重命名会话
const confirmRenameSession = async () => {
  if (!newSessionTitle.value.trim()) {
    ElMessage.warning('会话名称不能为空')
    return
  }
  
  try {
    await chatApi.updateSession(sessionToRename.value.id, newSessionTitle.value)
    
    // 更新会话列表中的名称
    const session = chatSessions.value.find(s => s.id === sessionToRename.value.id)
    if (session) {
      session.title = newSessionTitle.value
    }
    
    renameDialogVisible.value = false
    ElMessage.success('重命名成功')
  } catch (error) {
    console.error('重命名会话失败:', error)
    ElMessage.error('重命名会话失败')
  }
}

// 使用示例问题
const useExample = (question) => {
  userInput.value = question
  // 使用nextTick确保DOM更新后再尝试聚焦
  nextTick(() => {
    // 增加更健壮的检查，确保元素存在且方法可用
    if (centerInputRef.value && typeof centerInputRef.value.focus === 'function') {
      try {
        centerInputRef.value.focus()
      } catch (error) {
        console.error('聚焦输入框失败:', error)
      }
    }
  })
}

// 聚焦输入框
const focusInput = () => {
  nextTick(() => {
    if (chatMessages.length === 0 && centerInputRef.value) {
      centerInputRef.value.focus()
    } else if (inputRef.value) {
      inputRef.value.focus()
    }
  })
}

// 发送消息（流式响应版本）
const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || loading.value) return

  // 如果没有会话ID，先创建会话
  if (!currentSessionId.value) {
    try {
      const response = await chatApi.createSession('新对话')
      currentSessionId.value = response.data.data.id
      chatSessions.value.unshift({
        id: response.data.data.id,
        title: response.data.data.title,
        created_at: response.data.data.created_at
      })
    } catch (error) {
      ElMessage.error('创建会话失败，请稍后再试')
      return
    }
  }

  // 添加用户消息到聊天记录
  chatMessages.push({
    type: 'user',
    content: message
  })

  // 清空输入框
  userInput.value = ''

  // 设置加载状态
  loading.value = true

  // 自动滚动到底部
  await nextTick()
  scrollToBottom()

  // 添加AI响应占位
  const aiMessageIndex = chatMessages.length
  let aiContent = ''

  // 先插入空字符串，后续直接渲染为HTML
  chatMessages.push({
    type: 'system',
    content: ''
  })

  try {
    // 准备流式请求
    const { url, options } = chatApi.sendStreamMessage(currentSessionId.value, message)
    const response = await fetch(url, options)
    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`)
    }
    const reader = response.body.getReader()
    let decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value)
      buffer += text
      let lines = buffer.split('\n\n')
      buffer = lines.pop() // 剩余部分留给下次

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const content = line.slice(6)
          aiContent += content
          // 实时渲染markdown
          if (aiMessageIndex < chatMessages.length) {
            chatMessages[aiMessageIndex].content = aiContent
          }
          await nextTick()
          scrollToBottom()
        }
      }
    }
    // 流式输出结束后，刷新会话列表和当前会话消息
    await loadChatSessions()
    await refreshCurrentSessionMessages()
  } catch (error) {
    console.error('流式消息接收失败:', error)
    if (aiMessageIndex < chatMessages.length) {
      chatMessages[aiMessageIndex].content = '消息发送失败，请稍后再试'
    }
    ElMessage.error('发送消息失败，请稍后再试')
  } finally {
    loading.value = false
    nextTick(() => {
      scrollToBottom()
    })
  }
}

// 刷新当前会话的消息
const refreshCurrentSessionMessages = async () => {
  if (!currentSessionId.value) return
  
  try {
    const response = await chatApi.getSession(currentSessionId.value)
    
    if (response.data && response.data.data) {
      const sessionData = response.data.data
      
      // 更新消息列表，保留UI的滚动位置等状态
      chatMessages.length = 0
      
      if (sessionData.messages && sessionData.messages.length > 0) {
        sessionData.messages.forEach(msg => {
          chatMessages.push({
            type: msg.is_user ? 'user' : 'system',
            content: msg.content
          })
        })
      }
      
      // 滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
    }
  } catch (error) {
    console.error('刷新会话消息失败:', error)
    // 这里不显示错误消息，因为主要流程已经完成，这只是一个额外的刷新操作
  }
}

// Markdown渲染函数
const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    return md.render(text)
  } catch (error) {
    console.error('Markdown渲染失败:', error)
    return text
  }
}

// 滚动到底部
const scrollToBottom = () => {
  if (chatContentRef.value) {
    chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight
  }
}

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
    ElMessage.success('已退出登录')
  }).catch(() => {})
}

// 监听消息列表变化，自动滚动到底部
watch(() => chatMessages.length, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

// 获取最近的聊天会话
const fetchLatestSession = async () => {
  try {
    const response = await chatApi.getSessions()
    if (response.data && response.data.data && response.data.data.length > 0) {
      // 获取最新的会话
      const latestSession = response.data.data[0]
      currentSessionId.value = latestSession.id
      
      // 获取会话的消息历史
      const sessionDetail = await chatApi.getSession(latestSession.id)
      if (sessionDetail.data && sessionDetail.data.data && sessionDetail.data.data.messages) {
        // 清空当前消息列表
        chatMessages.length = 0
        
        // 添加历史消息
        sessionDetail.data.data.messages.forEach(msg => {
          chatMessages.push({
            type: msg.is_user ? 'user' : 'system',
            content: msg.content
          })
        })
      }
    } else {
      // 没有会话，将在发送第一条消息时创建
      currentSessionId.value = null
    }
  } catch (error) {
    console.error('获取聊天会话失败:', error)
    ElMessage.error('获取聊天历史失败')
  }
}

onMounted(async () => {
  // 检查用户是否已登录
  if (!localStorage.getItem('token')) {
    router.push('/login')
    return
  }
  
  // 加载会话列表
  await loadChatSessions()
  
  // 加载最近的聊天会话
  await fetchLatestSession()
})
</script>

<style scoped>
.web-container {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  position: fixed;
  background-color: #f5f7fa;
}

/* 侧边栏样式 */
.sidebar {
  width: 300px;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: width 0.3s;
  z-index: 100;
}
.sidebar-collapsed {
  width: 64px;
}
.sidebar-header {
  padding: 16px;
  text-align: center;
  border-bottom: 1px solid #eee;
  background-color: #1890ff;
  color: #fff;
}
.sidebar-header h1 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.sidebar-content {
  flex: 1;
  overflow-y: auto;
}
.sidebar-menu {
  border-right: none;
}
.sidebar-menu :deep(.el-menu-item.is-active) {
  color: #1890ff;
}
.sidebar-footer {
  padding: 12px;
  border-top: 1px solid #eee;
  overflow: hidden;
}
.user-panel {
  display: flex;
  align-items: center;
}
.user-emoji {
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-info {
  margin-left: 10px;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.username {
  font-size: 14px;
  line-height: 1.2;
  color: #333;
  font-weight: 500;
}
.user-status {
  font-size: 12px;
  color: #555;
  cursor: pointer;
  display: flex;
  align-items: center;
}
.status-dot {
  width: 8px;
  height: 8px;
  background-color: #52c41a;
  border-radius: 50%;
  margin-right: 4px;
  display: inline-block;
}

/* 侧边栏切换按钮 */
.sidebar-toggle {
  position: absolute;
  left: 300px; /* 固定在最左侧 */
  top: 50%;
  transform: translateY(-50%);
  background-color: #fff;
  border-radius: 0 4px 4px 0;
  width: 20px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 2px 0 8px rgba(0,0,0,0.15);
  z-index: 99;
  transition: left 0.3s;
}

/* 历史会话部分样式 */
.history-section {
  padding: 10px 0;
  border-top: 1px solid #f0f0f0;
}
.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 20px;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}
.new-session-btn {
  color: #1890ff;
  padding: 2px;
  transition: color 0.2s, transform 0.2s;
}
.new-session-btn:hover {
  color: #40a9ff;
  transform: scale(1.1);
}
.new-session-btn :deep(.el-icon) {
  font-size: 16px;
  border-radius: 50%;
  background-color: #e6f7ff;
  padding: 4px;
}
.session-list {
  max-height: calc(100vh - 250px);
  overflow-y: auto;
  padding-top: 4px;
}
.session-item {
  display: flex;
  align-items: center;
  padding: 10px 20px;
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 13px;
  color: #333;
}
.session-item:hover {
  background-color: #f5f7fa;
}
.session-item.active {
  background-color: #e6f7ff;
}
.session-title {
  margin-left: 8px;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #333;
}
.session-actions {
  display: none;
  margin-left: 8px;
}
.session-item:hover .session-actions {
  display: block;
}
.no-sessions {
  padding: 10px 20px;
  color: #666;
  font-size: 13px;
  text-align: center;
}

/* 适配侧边栏折叠状态 */
.sidebar-collapsed .history-header span,
.sidebar-collapsed .session-title {
  display: none;
}

/* 主内容区域样式 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  margin: 16px 16px 16px 20px;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.08);
  overflow: hidden;
  transition: margin-left 0.3s;
}
.content-expanded {
  margin-left: 180px;
}

/* 欢迎页样式 */
.welcome {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}
.welcome-container {
  max-width: 700px;
  width: 100%;
  text-align: center;
}
.welcome-header {
  margin-bottom: 30px;
}
.welcome-header h2 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 12px;
  background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.welcome-header p {
  font-size: 16px;
  color: #333;
}
.center-search {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}
.welcome-input {
  width: 100%;
  max-width: 600px;
  margin-bottom: 16px;
}
.welcome-input :deep(.el-textarea__inner) {
  font-size: 16px;
  padding: 16px;
  border-radius: 12px;
  border: 2px solid #eaeaea;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  transition: border-color 0.3s, box-shadow 0.3s;
}
.welcome-input :deep(.el-textarea__inner:focus) {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24,144,255,0.1);
}
.welcome-button {
  font-size: 16px;
  height: 48px;
  padding: 0 32px;
  border-radius: 24px;
  background: linear-gradient(135deg, #1890ff 0%, #722ed1 100%);
  border: none;
  transition: transform 0.3s, box-shadow 0.3s;
}
.welcome-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24,144,255,0.2);
}
.quick-examples {
  margin-top: 20px;
}
.quick-examples h3 {
  font-size: 18px;
  margin-bottom: 16px;
  color: #222;
}
.examples-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}
.example-item {
  background-color: #f5f7fa;
  padding: 12px 18px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: background 0.2s, border-color 0.2s, color 0.2s, transform 0.2s;
  border: 1px solid #eee;
}
.example-item:hover {
  background-color: #e6f7ff;
  border-color: #1890ff;
  color: #1890ff;
  transform: translateY(-2px);
}

/* 聊天区域样式 */
.chat-content {
  margin: 0 100px;
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  scroll-behavior: smooth;
}
.custom-scrollbar {
  position: relative;
  margin-right: 0px;
  overflow-y: scroll;
  scrollbar-width: fat;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}
.message-list {
  display: flex;
  flex-direction: column;
  margin-left: 80px;
  margin-right: 120px;
  gap: 20px;
}
.message {
  display: flex;
  gap: 12px;
  max-width: 90%;
}
.message-emoji {
  font-size: 24px;
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  position: relative;
  margin-left: 0px; /* 向左移动Emoji */
}
.user-message-emoji {
  font-size: 24px;
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  position: relative;
  margin-right: 80px; /* 向左移动Emoji */
}
.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.user-content {
  background-color: #1890ff;
  color: white;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);
  margin-right: 0px;
}
.ai-message {
  align-self: flex-start;
}
.ai-content {
  background-color: transparent;
  color: #333;
}
.message-content {
  border-radius: 12px;
  padding: 14px 20px;
  position: relative;
  max-width: calc(100% - 40px);
}
.message-text {
  word-break: break-word;
  line-height: 1.5;
}

/* 输入区域样式 */
.chat-input-area {
  padding: 20px;
  border-top: 1px solid #eee;
  background-color: #fff;
}

.chat-input-area :deep(.el-textarea__inner) {
  border-radius: 8px;
  padding: 12px;
  border: 1px solid #dcdfe6;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.chat-input-area :deep(.el-textarea__inner:focus) {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}
.input-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
.input-actions .el-button {
  border-radius: 8px;
  padding: 10px 20px;
}

/* Markdown样式 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: #222;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
}
.markdown-body :deep(h1) { font-size: 1.5em; }
.markdown-body :deep(h2) { font-size: 1.3em; }
.markdown-body :deep(h3) { font-size: 1.2em; }
.markdown-body :deep(p) {
  margin-top: 0;
  margin-bottom: 16px;
  color: #222;
}
.markdown-body :deep(pre) {
  padding: 16px;
  overflow: auto;
  background-color: #f6f8fa;
  border-radius: 3px;
  margin-bottom: 16px;
}
.markdown-body :deep(code) {
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  background-color: rgba(27, 31, 35, 0.05);
  border-radius: 3px;
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
}
.markdown-body :deep(pre code) {
  padding: 0;
  background-color: transparent;
}
.markdown-body :deep(blockquote) {
  padding: 0 1em;
  color: #444;
  border-left: 0.25em solid #dfe2e5;
  margin: 0 0 16px 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 2em;
  margin-bottom: 16px;
}
.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}
.markdown-body :deep(table th),
.markdown-body :deep(table td) {
  padding: 6px 13px;
  border: 1px solid #dfe2e5;
}
.markdown-body :deep(table tr) {
  background-color: #fff;
  border-top: 1px solid #c6cbd1;
}
.markdown-body :deep(table tr:nth-child(2n)) {
  background-color: #f6f8fa;
}
</style>
