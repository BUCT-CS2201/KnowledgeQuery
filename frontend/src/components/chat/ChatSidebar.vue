<template>
  <div class="sidebar" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <div class="sidebar-header">
      <h1>✨ 知识问答系统</h1>
      <div class="sidebar-toggle" @click="toggleSidebar">
        <el-icon :size="18">
          <Fold v-if="!sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </div>
    </div>
    <div class="sidebar-content">
      <!-- 主导航菜单 -->
      <div class="main-menu">
        <!-- 新建会话按钮 -->
        <div class="chat-button chat-button-1" @click="createNewSession(1)">
          <span class="icon">🧩</span>
          <span class="text">新建会话</span>
        </div>
        
        <!-- 新建知识库问答按钮 -->
        <div class="chat-button chat-button-2" @click="createNewSession(2)">
          <span class="icon">📂</span>
          <span class="text">新建知识库问答</span>
        </div>
        
        <!-- 新建知识图谱问答按钮 -->
        <div class="chat-button chat-button-3" @click="createNewSession(3)">
          <span class="icon">🌐</span>
          <span class="text">新建知识图谱问答</span>
        </div>
        
        <!-- 历史会话部分 -->
        <div class="menu-item history-title">
          <span class="menu-icon">🗂️</span>
          <span class="menu-text">历史会话</span>
        </div>
        
        <!-- 历史会话列表 -->
        <div class="submenu">
          <div
            v-for="session in chatSessions"
            :key="session.id"
            :class="['submenu-item', currentSessionId === session.id ? 'active' : '']"
            @click="switchSession(session.id)"
          >
            <span class="session-type-emoji">{{ getSessionTypeEmoji(session.type) }}</span>
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
    </div>
    <div class="sidebar-footer">
      <div class="user-panel" @click="toggleUserMenu">
        <span class="user-emoji">👤</span>
        <div class="user-info">
          <div class="username">{{ user?.name || '未登录' }}</div>
          <div class="user-status">
            <span class="status-dot"></span> 在线
          </div>
        </div>
        <!-- 用户菜单 -->
        <div class="user-menu" v-if="showUserMenu">
          <div class="user-menu-item" @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            <span>退出登录</span>
          </div>
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
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { chatApi } from '../../services/api'
import { 
  ChatDotSquare,
  ChatLineRound,
  Edit,
  Delete,
  Plus,
  MoreFilled,
  SwitchButton,
  Fold,  // 添加折叠图标
  Expand  // 添加展开图标
} from '@element-plus/icons-vue'

// 会话类型对应的Emoji
const SESSION_TYPE_EMOJIS = {
  1: '🧩', // 普通问答
  2: '📂', // 知识库问答
  3: '🌐', // 知识图谱问答
  'default': '🧩' // 默认Emoji
}

// 会话类型对应的默认标题
const SESSION_TYPE_TITLES = {
  1: '新对话',
  2: '新知识库问答',
  3: '新知识图谱问答'
}

const props = defineProps({
  currentSessionId: {
    type: String,
    default: null
  },
  chatSessions: {
    type: Array,
    default: () => []
  },
  sidebarCollapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:sidebarCollapsed', 
  'update:currentSessionId', 
  'session-switched', 
  'session-created', 
  'session-deleted', 
  'session-renamed',
  'logout'
])

const router = useRouter()
const activeMenu = ref('chat')
const renameDialogVisible = ref(false)
const newSessionTitle = ref('')
const sessionToRename = ref(null)
const showUserMenu = ref(false)

// 从本地存储获取用户信息
const user = computed(() => {
  const userStr = localStorage.getItem('user')
  return userStr ? JSON.parse(userStr) : null
})

// 获取会话类型对应的Emoji
const getSessionTypeEmoji = (type) => {
  return SESSION_TYPE_EMOJIS[type] || SESSION_TYPE_EMOJIS.default
}

// 激活聊天页面
const activateChat = () => {
  activeMenu.value = 'chat'
}

// 切换会话
const switchSession = (sessionId) => {
  if (props.currentSessionId === sessionId) return
  emit('update:currentSessionId', sessionId)
  emit('session-switched', sessionId)
}

// 创建新会话
const createNewSession = async (sessionType = 1) => {
  try {
    const title = SESSION_TYPE_TITLES[sessionType] || '新对话'
    
    const response = await chatApi.createSession(title, sessionType)
    if (response.data && response.data.data) {
      const newSession = response.data.data
      emit('session-created', newSession)
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
      emit('session-deleted', sessionId)
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
    emit('session-renamed', { id: sessionToRename.value.id, title: newSessionTitle.value })
    renameDialogVisible.value = false
    ElMessage.success('重命名成功')
  } catch (error) {
    console.error('重命名会话失败:', error)
    ElMessage.error('重命名会话失败')
  }
}

// 显示/隐藏用户菜单
const toggleUserMenu = (event) => {
  event.stopPropagation()
  showUserMenu.value = !showUserMenu.value
  
  // 点击外部区域关闭菜单
  if (showUserMenu.value) {
    setTimeout(() => {
      const closeMenu = () => {
        showUserMenu.value = false
        document.removeEventListener('click', closeMenu)
      }
      document.addEventListener('click', closeMenu)
    }, 0)
  }
}

// 切换侧边栏显示/隐藏
const toggleSidebar = () => {
  emit('update:sidebarCollapsed', !props.sidebarCollapsed)
}

// 退出登录
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
    customClass: 'custom-message-box',
    confirmButtonClass: 'custom-confirm-button',
    cancelButtonClass: 'custom-cancel-button'
  }).then(() => {
    emit('logout')
  }).catch(() => {})
}
</script>

<style scoped>
.sidebar {
  width: 350px;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  transition: all 0.3s;
  z-index: 100;
  height: 100vh;
  border-right: 1px solid #eeeeee;
  position: relative;
}

.sidebar-collapsed {
  width: 0;
  padding: 0;
  overflow: hidden;
  border-right: none;
  transform: translateX(-100%);
}

.sidebar-header {
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eeeeee;
  background-color: #212121;
  color: #ffffff;
}

.sidebar-header h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  background-color: rgba(255, 255, 255, 0.1);
  transition: all 0.3s;
  color: #ffffff;
}

.sidebar-toggle:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.sidebar-content {
  flex: 1;
  /* 移除内容区域的滚动条 */
  overflow-y: hidden;
}

/* 主菜单样式 */
.main-menu {
  padding: 16px 12px;
}

/* 新会话按钮样式 - 简约风格 */
.chat-button {
  display: inline-flex;
  align-items: center;
  padding: 10px 16px; /* 从8px 14px增加到10px 16px */
  margin-bottom: 10px; /* 从8px增加到10px */
  border: none; /* 移除边框 */
  border-radius: 10px; /* pill shape */
  color: #1f1f1f;
  font-size: 15px; /* 从14px增加到15px */
  font-family: sans-serif;
  cursor: pointer;
  transition: all 0.2s ease;
  gap: 10px; /* 从8px增加到10px */
  width: 100%;
}

/* 三种不同颜色的按钮背景 */
.chat-button-1 {
  background-color: rgb(70, 158, 180);
  color: white; /* 按钮文字改为白色，更易读 */
}

.chat-button-2 {
  background-color: rgb(135, 207, 164);
  color: #333333; /* 浅色背景配深色文字 */
}

.chat-button-3 {
  background-color: rgb(254, 232, 154);
  color: #333333; /* 浅色背景配深色文字 */
}

.chat-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  filter: brightness(1.05);
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 14px 16px; /* 从12px 14px增加到14px 16px */
  cursor: pointer;
  transition: all 0.3s;
  font-size: 15px; /* 从14px增加到15px */
  color: #333333;
  border-left: 3px solid transparent;
}

.menu-item:hover {
  background-color: #f5f5f5;
  border-left-color: #212121;
}

.menu-icon {
  font-size: 20px; /* 从18px增加到20px */
  margin-right: 12px;
}

.menu-text {
  flex: 1;
}

.history-title {
  font-weight: 500;
  color: #212121;
  margin-top: 18px; /* 从16px增加到18px */
  border-top: 1px solid #eeeeee;
  padding-top: 18px; /* 从16px增加到18px */
}

/* 子菜单样式 */
.submenu {
  margin-top: 4px;
  /* 仅保留历史会话列表的滚动条 */
  max-height: calc(100vh - 350px);
  overflow-y: auto;
}

.submenu-item {
  display: flex;
  align-items: center;
  padding: 12px 16px 12px 26px; /* 从10px 14px 10px 24px增加 */
  cursor: pointer;
  transition: background-color 0.3s;
  font-size: 14px; /* 从13px增加到14px */
  color: #424242;
  border-left: 2px solid transparent;
  margin-bottom: 2px;
  border-radius: 4px;
}

.submenu-item:hover {
  background-color: #f5f5f5;
}

.submenu-item.active {
  background-color: #f0f0f0;
  border-left-color: #424242;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #eeeeee;
  position: relative;
}

.user-panel {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 10px; /* 从8px增加到10px */
  border-radius: 8px;
  transition: all 0.3s;
}

.user-panel:hover {
  background-color: #f5f5f5;
}

.user-emoji {
  font-size: 20px; /* 从18px增加到20px */
  background-color: #f0f0f0;
  border-radius: 50%;
  height: 40px; /* 从36px增加到40px */
  width: 40px; /* 从36px增加到40px */
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info {
  margin-left: 12px;
  flex: 1;
}

.username {
  font-size: 15px; /* 从14px增加到15px */
  line-height: 1.2;
  color: #212121;
  font-weight: 500;
}

.user-status {
  font-size: 13px; /* 从12px增加到13px */
  color: #616161;
  display: flex;
  align-items: center;
  margin-top: 4px;
}

.status-dot {
  width: 8px;
  height: 8px;
  background-color: #424242;
  border-radius: 50%;
  margin-right: 4px;
  display: inline-block;
}

/* 用户菜单 */
.user-menu {
  position: absolute;
  bottom: 70px;
  left: 16px;
  right: 16px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  z-index: 10;
  border: 1px solid #eeeeee;
}

.user-menu-item {
  display: flex;
  align-items: center;
  padding: 14px 18px; /* 从12px 16px增加到14px 18px */
  cursor: pointer;
  transition: background-color 0.3s;
  color: #212121;
  font-size: 15px; /* 添加字体大小 */
}

.user-menu-item:hover {
  background-color: #f5f5f5;
}

.user-menu-item .el-icon {
  margin-right: 8px;
  font-size: 16px;
  color: #424242;
}

/* 会话项样式 */
.session-title {
  margin-left: 8px;
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-actions {
  display: none;
  margin-left: 8px;
  color: #616161;
}

.submenu-item:hover .session-actions {
  display: block;
}

.no-sessions {
  padding: 10px 20px 10px 24px;
  color: #9e9e9e;
  font-size: 13px;
  font-style: italic;
}

/* 会话类型Emoji样式 */
.session-type-emoji {
  font-size: 18px; /* 从16px增加到18px */
}

/* 自定义滚动条样式 */
.submenu::-webkit-scrollbar {
  width: 8px; /* 从6px增加到8px */
}

.submenu::-webkit-scrollbar-track {
  background: #f9f9f9;
  border-radius: 4px; /* 从3px增加到4px */
}

.submenu::-webkit-scrollbar-thumb {
  background: #e0e0e0;
  border-radius: 4px; /* 从3px增加到4px */
}

.submenu::-webkit-scrollbar-thumb:hover {
  background: #d0d0d0;
}

/* El-dropdown样式覆盖 */
:deep(.el-dropdown-menu) {
  background-color: #ffffff;
  border: 1px solid #eeeeee;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-dropdown-menu__item) {
  color: #212121;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: #f5f5f5;
  color: #000000;
}

:deep(.el-button--primary) {
  background-color: #212121;
  border-color: #212121;
}

:deep(.el-button--primary:hover) {
  background-color: #424242;
  border-color: #424242;
}

/* 适配侧边栏折叠状态 */
.sidebar-collapsed .menu-text,
.sidebar-collapsed .session-title,
.sidebar-collapsed .user-info,
.sidebar-collapsed .text {
  display: none;
}

.sidebar-collapsed .submenu-item {
  padding: 10px 0;
  justify-content: center;
}

.sidebar-collapsed .menu-item {
  padding: 12px 0;
  justify-content: center;
}

.sidebar-collapsed .menu-icon {
  margin-right: 0;
}

.sidebar-collapsed .user-panel {
  justify-content: center;
}

.sidebar-collapsed .chat-button {
  padding: 8px 0;
  justify-content: center;
}

.sidebar-collapsed .chat-button .icon {
  margin-right: 0;
}

.custom-message-box {
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
  background-color: rgba(255, 255, 255, 0.92);
  font-family: 'SimSun', '宋体', serif;
}
.custom-confirm-button {
  border-radius: 50px;
  background: #111;
  border: none;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  transition: 0.3s;
  color: #fff;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.10);
}
.custom-confirm-button:hover {
  background: #444;
  color: #fff;
}
.custom-cancel-button {
  border-radius: 50px;
  background: #e0e0e0;
  border: none;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 1px;
  transition: 0.3s;
  color: #222;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.10);
}
.custom-cancel-button:hover {
  background: #ccc;
  color: #000;
}

/* 响应式设计 - 媒体查询 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    width: 280px;
  }
  
  .sidebar-collapsed {
    width: 0;
    transform: translateX(-100%);
    border-right: none;
  }
  
  .sidebar-collapsed .sidebar-content,
  .sidebar-collapsed .sidebar-footer,
  .sidebar-collapsed .sidebar-header h1 {
    opacity: 0;
  }
  
  .sidebar-collapsed .sidebar-toggle {
    opacity: 0;
    visibility: hidden;
  }
}

@media (max-width: 480px) {
  .chat-button {
    font-size: 14px;
    padding: 8px 12px;
  }
  
  .sidebar-header h1 {
    font-size: 16px;
  }
  
  .menu-item, .submenu-item {
    padding: 10px 12px;
  }
  
  .user-panel {
    padding: 8px;
  }
}
</style>
