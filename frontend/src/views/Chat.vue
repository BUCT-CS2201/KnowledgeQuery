<template>
  <div class="web-container">
    <!-- 侧边栏组件 -->
    <ChatSidebar 
      :currentSessionId="currentSessionId"
      :chatSessions="chatSessions"
      :sidebarCollapsed="sidebarCollapsed"
      @update:currentSessionId="currentSessionId = $event"
      @update:sidebarCollapsed="sidebarCollapsed = $event"
      @session-switched="handleSessionSwitch"
      @session-created="handleSessionCreated"
      @session-deleted="handleSessionDeleted"
      @session-renamed="handleSessionRenamed"
      @logout="handleLogout"
    />

    <!-- 侧边栏伸缩按钮 -->
    <div class="sidebar-toggle" @click="toggleSidebar" 
         :style="{ left: sidebarCollapsed ? '64px' : '300px' }">
      <el-icon v-if="sidebarCollapsed"><ArrowRight /></el-icon>
      <el-icon v-else><ArrowLeft /></el-icon>
    </div>

    <!-- 主对话组件 -->
    <ChatMain 
      ref="chatMainRef"
      :currentSessionId="currentSessionId"
      :sidebarCollapsed="sidebarCollapsed"
      :sessionType="currentSessionType"
      @session-created="handleSessionCreated"
      @messages-updated="handleMessagesUpdated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { chatApi } from '../services/api'
import ChatSidebar from '../components/chat/ChatSidebar.vue'
import ChatMain from '../components/chat/ChatMain.vue'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()
const chatMainRef = ref(null)
const currentSessionId = ref(null)
const chatSessions = ref([])
const sidebarCollapsed = ref(false)

// 计算当前会话类型
const currentSessionType = computed(() => {
  if (!currentSessionId.value) return 1
  const currentSession = chatSessions.value.find(s => s.id === currentSessionId.value)
  return currentSession?.type || 1
})

// 切换侧边栏的展开/折叠状态
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 处理会话切换
const handleSessionSwitch = async (sessionId) => {
  try {
    const response = await chatApi.getSession(sessionId)
    
    if (response.data && response.data.data) {
      const sessionData = response.data.data
      
      // 加载消息到主组件
      if (sessionData.messages && sessionData.messages.length > 0) {
        chatMainRef.value.loadMessages(sessionData.messages)
      } else {
        chatMainRef.value.loadMessages([])
      }
    }
  } catch (error) {
    console.error('加载会话消息失败:', error)
    ElMessage.error('加载会话消息失败')
  }
}

// 处理会话创建
const handleSessionCreated = (newSession) => {
  // 添加新会话到列表，确保包含类型信息
  chatSessions.value.unshift({
    id: newSession.id,
    title: newSession.title,
    type: newSession.type || 1,
    created_at: newSession.created_at,
    updated_at: newSession.updated_at
  })
  
  // 将当前会话ID设置为新会话ID
  currentSessionId.value = newSession.id
  
  // 清空消息列表
  chatMainRef.value.loadMessages([])
}

// 处理会话删除
const handleSessionDeleted = (sessionId) => {
  // 从会话列表中删除
  chatSessions.value = chatSessions.value.filter(s => s.id !== sessionId)
  
  // 如果删除的是当前会话，清空消息并重置当前会话ID
  if (currentSessionId.value === sessionId) {
    currentSessionId.value = null
    chatMainRef.value.loadMessages([])
  }
}

// 处理会话重命名
const handleSessionRenamed = ({ id, title }) => {
  const session = chatSessions.value.find(s => s.id === id)
  if (session) {
    session.title = title
  }
}

// 处理消息更新
const handleMessagesUpdated = async () => {
  await loadChatSessions()  // 刷新会话列表
}

// 加载所有聊天会话
const loadChatSessions = async () => {
  try {
    const response = await chatApi.getSessions()
    if (response.data && response.data.data) {
      // 确保所有会话都有类型字段，默认为1
      chatSessions.value = response.data.data.map(session => ({
        ...session,
        type: session.type || 1
      }))
    }
  } catch (error) {
    console.error('获取聊天会话列表失败:', error)
    ElMessage.error('获取会话列表失败')
  }
}

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
        // 加载消息到主组件
        chatMainRef.value.loadMessages(sessionDetail.data.data.messages)
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

// 退出登录
const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
  ElMessage.success('已退出登录')
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

/* 侧边栏切换按钮 */
.sidebar-toggle {
  position: absolute;
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
</style>
