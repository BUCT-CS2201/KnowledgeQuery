<template>
  <div class="chat-container">
    <!-- 侧边栏 -->
    <aside class="chat-sidebar">
      <div class="sidebar-header">
        <button class="new-chat-btn" @click="createNewChat">
          <el-icon><Plus /></el-icon> 新建对话
        </button>
      </div>
      
      <div class="session-list" v-if="sessions.length > 0">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: currentSession && currentSession.id === session.id }"
          @click="selectSession(session.id)"
        >
          <div class="session-info">
            <el-icon><ChatDotRound /></el-icon>
            <span class="session-title">{{ session.title }}</span>
          </div>
          <div class="session-actions">
            <el-popconfirm
              title="确定要删除这个对话吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="deleteSession(session.id)"
            >
              <template #reference>
                <el-button
                  class="delete-btn"
                  circle
                  size="small"
                  @click.stop
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </div>
      
      <div class="sidebar-empty" v-else>
        <div class="empty-text">暂无对话记录</div>
      </div>
      
      <div class="sidebar-footer">
        <div class="user-info">
          <el-avatar :size="32" :src="userAvatarUrl"></el-avatar>
          <span>{{ user ? user.username : '用户' }}</span>
        </div>
      </div>
    </aside>
    
    <!-- 主聊天区域 -->
    <main class="chat-main">
      <template v-if="currentSession">
        <!-- 模型选择栏 -->
        <div class="model-selector">
          <el-select v-model="selectedModel" placeholder="选择模型" size="small">
            <el-option label="通用知识模型" value="general" />
            <el-option label="DeepSeek" value="deepseek" />
            <el-option label="代码助手" value="code" />
            <el-option label="文档理解" value="doc" />
          </el-select>
          
          <el-switch
            v-model="enableWebSearch"
            active-text="联网搜索"
            inactive-text="仅知识库"
            size="small"
            style="margin-left: 16px;"
          />
          
          <el-switch
            v-model="enableStreamOutput"
            active-text="流式输出"
            inactive-text="一次性输出"
            size="small"
            style="margin-left: 16px;"
            v-if="selectedModel === 'deepseek'"
          />
        </div>

        <!-- 聊天消息区域 -->
        <div class="chat-messages" ref="messagesContainer">
          <div class="chat-welcome" v-if="messages.length === 0">
            <h2>欢迎使用知识问答子系统</h2>
            <p>您可以向AI提问任何问题，系统将从知识库中为您寻找答案</p>
            <div class="welcome-features">
              <div class="feature-item">
                <el-icon><Document /></el-icon>
                <span>上传文件获取精准回答</span>
              </div>
              <div class="feature-item">
                <el-icon><Search /></el-icon>
                <span>开启联网搜索获取最新信息</span>
              </div>
              <div class="feature-item">
                <el-icon><Select /></el-icon>
                <span>选择专业模型解决特定问题</span>
              </div>
            </div>
          </div>
          
          <template v-else>
            <div
              v-for="(message, index) in messages"
              :key="index"
              class="message"
              :class="message.is_user ? 'user-message' : 'ai-message'"
            >
              <div class="message-avatar">
                <el-avatar
                  :size="36"
                  :src="message.is_user ? userAvatarUrl : aiAvatarUrl"
                ></el-avatar>
              </div>
              <div class="message-content">
                <div class="message-sender">
                  {{ message.is_user ? user.username : '知识助手' }}
                  <span v-if="!message.is_user && message.web_search" class="source-tag">
                    <el-icon><Connection /></el-icon> 联网搜索
                  </span>
                </div>
                <div class="message-text" v-html="formatMessage(message.content)"></div>
                
                <!-- 如果有引用来源，显示来源链接 -->
                <div v-if="!message.is_user && message.sources && message.sources.length > 0" class="message-sources">
                  <div class="sources-title">来源：</div>
                  <div v-for="(source, i) in message.sources" :key="i" class="source-item">
                    <a :href="source.url" target="_blank" class="source-link">
                      <el-icon><Link /></el-icon>
                      {{ source.title || source.url }}
                    </a>
                  </div>
                </div>
                
                <!-- 如果有上传的文件，显示文件信息 -->
                <div v-if="message.is_user && message.files && message.files.length > 0" class="message-files">
                  <div class="files-title">上传的文件：</div>
                  <div v-for="(file, i) in message.files" :key="i" class="file-item">
                    <el-icon><Document /></el-icon>
                    {{ file.name }}
                    <span class="file-size">{{ formatFileSize(file.size) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
        
        <!-- 输入区域 -->
        <div class="chat-input-area">
          <el-input
            v-model="userInput"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            resize="none"
            @keydown.enter.ctrl.exact="sendUserMessage"
          ></el-input>
          
          <!-- 文件上传和发送按钮区域 -->
          <div class="input-actions">
            <div class="input-left">
              <el-upload
                ref="upload"
                action="#"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleFileChange"
                :multiple="true"
              >
                <el-button class="upload-btn" :disabled="loading">
                  <el-icon><Upload /></el-icon>
                  上传文件
                </el-button>
              </el-upload>
              
              <div v-if="selectedFiles.length > 0" class="selected-files">
                已选择 {{ selectedFiles.length }} 个文件
                <el-button type="text" @click="clearSelectedFiles" class="clear-files">
                  清除
                </el-button>
              </div>
              <div v-else class="input-tip">Ctrl + Enter 发送</div>
            </div>
            
            <el-button
              class="send-btn"
              type="primary"
              :disabled="!userInput.trim() && selectedFiles.length === 0"
              :loading="loading"
              @click="sendUserMessage"
            >
              发送
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="empty-chat" v-else>
        <div class="empty-chat-content">
          <el-icon class="empty-icon"><ChatDotRound /></el-icon>
          <h2>请创建新对话或从侧边栏选择对话</h2>
          <el-button type="primary" @click="createNewChat">创建新对话</el-button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useAuthStore } from '../store/auth'
import { useChatStore } from '../store/chat'
import { 
  Plus, 
  ChatDotRound, 
  Delete, 
  Upload, 
  Document, 
  Search, 
  Select, 
  Connection, 
  Link 
} from '@element-plus/icons-vue'

export default {
  name: 'ChatView',
  components: {
    Plus,
    ChatDotRound,
    Delete,
    Upload,
    Document,
    Search,
    Select,
    Connection,
    Link
  },
  setup() {
    const authStore = useAuthStore()
    const chatStore = useChatStore()
    const messagesContainer = ref(null)
    const userInput = ref('')
    const selectedFiles = ref([])
    const upload = ref(null)
    const selectedModel = ref('general')
    const enableWebSearch = ref(false)
    const enableStreamOutput = ref(true)
    
    const user = computed(() => authStore.getUser)
    const sessions = computed(() => chatStore.getSessions)
    const currentSession = computed(() => chatStore.getCurrentSession)
    const messages = computed(() => chatStore.getMessages)
    const loading = computed(() => chatStore.getLoading)
    
    // 用户头像URL（基于用户名生成颜色）
    const userAvatarUrl = computed(() => {
      if (!user.value) return ''
      const hash = hashCode(user.value.username)
      const hue = hash % 360
      return `https://ui-avatars.com/api/?name=${user.value.username}&background=${hslToHex(hue, 60, 60)}&color=fff`
    })
    
    // AI头像URL
    const aiAvatarUrl = computed(() => {
      return 'https://ui-avatars.com/api/?name=AI&background=0A84FF&color=fff'
    })
    
    // 处理文件变化
    const handleFileChange = (file) => {
      selectedFiles.value.push(file.raw)
    }
    
    // 清除选中的文件
    const clearSelectedFiles = () => {
      selectedFiles.value = []
      if (upload.value) {
        upload.value.clearFiles()
      }
    }
    
    // 创建新对话
    const createNewChat = async () => {
      try {
        await chatStore.createSession()
        scrollToBottom()
      } catch (error) {
        console.error('创建对话失败:', error)
        ElMessage.error('创建对话失败，请重试')
      }
    }
    
    // 选择会话
    const selectSession = async (sessionId) => {
      await chatStore.selectSession(sessionId)
      scrollToBottom()
    }
    
    // 删除会话
    const deleteSession = async (sessionId) => {
      await chatStore.deleteSession(sessionId)
    }
    
    // 格式化文件大小
    const formatFileSize = (size) => {
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
    
    // 发送用户消息
    const sendUserMessage = async () => {
      if ((!userInput.value.trim() && selectedFiles.value.length === 0) || loading.value) return
      
      // 如果没有当前会话，创建一个
      if (!currentSession.value) {
        await createNewChat()
      }
      
      const content = userInput.value
      userInput.value = ''
      
      // 准备要发送的消息数据
      const messageData = {
        content: content.trim(),
        model: selectedModel.value,
        web_search: enableWebSearch.value,
        stream: enableStreamOutput.value && selectedModel.value === 'deepseek',
        files: selectedFiles.value.length > 0 ? selectedFiles.value.map(f => ({
          name: f.name,
          size: f.size,
          type: f.type
        })) : undefined
      }
      
      // 显示等待提示
      if (messageData.stream && messageData.model === 'deepseek') {
        console.log('使用流式输出模式，正在等待响应...')
      }
      
      // 发送消息和文件
      try {
        if (selectedFiles.value.length > 0) {
          await chatStore.sendMessageWithFiles(messageData, selectedFiles.value)
          clearSelectedFiles()
        } else {
          await chatStore.sendMessage(messageData)
        }
        
        // 强制视图更新
        await nextTick()
        scrollToBottom()
        
        // 如果启用了流式输出，每200ms检查一次更新并滚动到底部
        if (messageData.stream && messageData.model === 'deepseek') {
          const checkInterval = setInterval(() => {
            if (!chatStore.loading) {
              clearInterval(checkInterval)
              scrollToBottom()
              return
            }
            scrollToBottom()
          }, 200)
          
          // 最多等待30秒
          setTimeout(() => {
            clearInterval(checkInterval)
          }, 30000)
        }
      } catch (error) {
        console.error('发送消息失败:', error)
      }
    }
    
    // 格式化消息（处理换行符等）
    const formatMessage = (content) => {
      if (!content) return ''
      // 将换行符替换为HTML的换行标签
      return content
        .replace(/\n/g, '<br>')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    }
    
    // 滚动到底部
    const scrollToBottom = async () => {
      await nextTick()
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
      }
    }
    
    // 监听消息列表变化，自动滚动到底部
    watch(messages, () => {
      scrollToBottom()
    })
    
    // 辅助函数：计算字符串的哈希值
    const hashCode = (str) => {
      let hash = 0
      for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i)
        hash |= 0 // 转为32位整数
      }
      return Math.abs(hash)
    }
    
    // 辅助函数：HSL颜色转HEX
    const hslToHex = (h, s, l) => {
      l /= 100
      const a = s * Math.min(l, 1 - l) / 100
      const f = n => {
        const k = (n + h / 30) % 12
        const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1)
        return Math.round(255 * color).toString(16).padStart(2, '0')
      }
      return `${f(0)}${f(8)}${f(4)}`
    }
    
    onMounted(async () => {
      // 获取会话列表
      await chatStore.fetchSessions()
      
      // 如果有会话，选择第一个
      if (sessions.value.length > 0) {
        await chatStore.selectSession(sessions.value[0].id)
      }
    })
    
    return {
      userInput,
      user,
      sessions,
      currentSession,
      messages,
      loading,
      messagesContainer,
      userAvatarUrl,
      aiAvatarUrl,
      selectedFiles,
      upload,
      selectedModel,
      enableWebSearch,
      enableStreamOutput,
      createNewChat,
      selectSession,
      deleteSession,
      sendUserMessage,
      formatMessage,
      handleFileChange,
      clearSelectedFiles,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  height: calc(100vh - 61px); /* 减去导航栏高度 */
  overflow: hidden;
}

/* 侧边栏样式 */
.chat-sidebar {
  width: 280px;
  background-color: #f7f8fa;
  border-right: 1px solid #e4e6eb;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e6eb;
}

.new-chat-btn {
  width: 100%;
  border: none;
  background-color: #0a84ff;
  color: white;
  padding: 10px;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background-color 0.3s;
}

.new-chat-btn:hover {
  background-color: #0071e3;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px 8px;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.session-item:hover {
  background-color: #e9ecef;
}

.session-item.active {
  background-color: #e0f2ff;
}

.session-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}

.session-title {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-actions {
  opacity: 0;
  transition: opacity 0.2s;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.delete-btn {
  padding: 4px;
  font-size: 12px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #e4e6eb;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

/* 主聊天区域样式 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #fff;
}

/* 模型选择栏 */
.model-selector {
  padding: 12px 16px;
  border-bottom: 1px solid #e4e6eb;
  display: flex;
  align-items: center;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  display: flex;
  margin-bottom: 24px;
  gap: 16px;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
}

.message-sender {
  font-weight: 600;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.source-tag {
  font-size: 12px;
  background-color: #e6f7ff;
  color: #0a84ff;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: normal;
  display: flex;
  align-items: center;
  gap: 4px;
}

.message-text {
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message-sources {
  margin-top: 12px;
  border-top: 1px solid #eee;
  padding-top: 8px;
}

.sources-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.source-item {
  margin-bottom: 6px;
}

.source-link {
  font-size: 13px;
  color: #0a84ff;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
}

.message-files {
  margin-top: 12px;
  background-color: #f0f2f5;
  padding: 8px 12px;
  border-radius: 6px;
}

.files-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  margin-bottom: 6px;
}

.file-size {
  color: #999;
  margin-left: 6px;
}

.user-message .message-sender {
  color: #333;
}

.ai-message {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
}

.ai-message .message-sender {
  color: #0a84ff;
}

.chat-welcome {
  text-align: center;
  padding: 40px 20px;
  color: #666;
}

.chat-welcome h2 {
  color: #333;
  margin-bottom: 16px;
}

.welcome-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 40px;
  max-width: 400px;
  margin: 40px auto 0;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background-color: #f0f7ff;
  padding: 16px;
  border-radius: 8px;
  text-align: left;
}

.feature-item .el-icon {
  font-size: 24px;
  color: #0a84ff;
}

.chat-input-area {
  padding: 16px;
  border-top: 1px solid #e4e6eb;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.input-tip {
  color: #999;
  font-size: 12px;
}

.selected-files {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}

.clear-files {
  padding: 0;
}

.send-btn {
  padding: 8px 20px;
}

.empty-chat {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f7f8fa;
}

.empty-chat-content {
  text-align: center;
  max-width: 400px;
}

.empty-icon {
  font-size: 48px;
  color: #999;
  margin-bottom: 16px;
}

pre {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
}

code {
  font-family: monospace;
}
</style> 