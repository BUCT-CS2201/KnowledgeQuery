<template>
  <div class="web-container">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h1>知识问答系统</h1>
      </div>
      <div class="sidebar-content">
        <el-menu default-active="1" class="sidebar-menu">
          <el-menu-item index="1">
            <el-icon><ChatDotSquare /></el-icon>
            <span>问答系统</span>
          </el-menu-item>
          <el-menu-item index="2">
            <el-icon><DocumentCopy /></el-icon>
            <span>历史记录</span>
          </el-menu-item>
        </el-menu>
      </div>
      <div class="sidebar-footer">
        <div class="user-panel">
          <el-avatar :size="32" icon="User" />
          <div class="user-info">
            <div class="username">{{ user?.name || '未登录' }}</div>
            <el-dropdown trigger="click">
              <span class="user-status">
                在线 <el-icon><ArrowDown /></el-icon>
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

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 聊天区域 -->
      <div class="chat-content" ref="chatContentRef">
        <div v-if="chatMessages.length === 0" class="welcome">
          <el-empty description="开始您的提问">
            <template #description>
              <p>欢迎使用博物馆知识问答系统</p>
            </template>
            <el-button type="primary">开始提问</el-button>
          </el-empty>
        </div>

        <div v-else class="message-list">
          <div
            v-for="(message, index) in chatMessages"
            :key="index"
            :class="['message', message.type === 'user' ? 'user-message' : 'system-message']"
          >
            <div class="message-avatar">
              <el-avatar :icon="message.type === 'user' ? 'User' : 'Service'" :size="32" />
            </div>
            <div class="message-content">
              <div class="message-header">
                <span class="message-name">{{ message.type === 'user' ? user?.name || '您' : '知识助手' }}</span>
              </div>
              <div class="message-text" v-html="message.content"></div>
            </div>
          </div>
        </div>

        <div v-if="loading" class="loading-indicator">
          <el-skeleton :rows="2" animated />
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="chat-input-area">
        <el-input
          v-model="userInput"
          placeholder="请输入您想了解的博物馆知识..."
          :disabled="loading"
          type="textarea"
          :rows="2"
          resize="none"
          @keyup.enter.ctrl.prevent="sendMessage"
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { chatApi } from '../services/api'
import { 
  ChatDotSquare, 
  DocumentCopy, 
  Position,
  ArrowDown,
  Service
} from '@element-plus/icons-vue'

const router = useRouter()
const loading = ref(false)
const userInput = ref('')
const chatContentRef = ref(null)
const chatMessages = reactive([])

// 从本地存储获取用户信息
const user = computed(() => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
})

// 发送消息
const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || loading.value) return
  
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
  
  try {
    // 模拟API响应
    setTimeout(() => {
      // 添加系统回复
      chatMessages.push({
        type: 'system',
        content: `以下是关于"${message}"的回答：<br><br>这是一个示例回答。在实际应用中，这里会显示从后端API获取的回答内容。`
      })
      
      loading.value = false
      
      // 自动滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
    }, 1500)
  } catch (error) {
    ElMessage.error('发送消息失败，请稍后再试')
    loading.value = false
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

onMounted(() => {
  // 可以在这里加载历史聊天记录
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
  width: 220px;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
}

.user-panel {
  display: flex;
  align-items: center;
}

.user-info {
  margin-left: 10px;
}

.username {
  font-size: 14px;
  line-height: 1.2;
}

.user-status {
  font-size: 12px;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
}

/* 主内容区域样式 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #fff;
  margin: 0 8px;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  overflow: hidden;
}

.chat-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.welcome {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 8px;
}

.message-content {
  background-color: #f9f9f9;
  padding: 12px;
  border-radius: 4px;
  max-width: 80%;
}

.user-message .message-content {
  background-color: #e6f7ff;
}

.message-header {
  margin-bottom: 6px;
}

.message-name {
  font-weight: 500;
  color: #333;
}

.message-text {
  line-height: 1.5;
}

.loading-indicator {
  padding: 16px 0;
}

.chat-input-area {
  padding: 16px;
  border-top: 1px solid #eee;
}

.input-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
