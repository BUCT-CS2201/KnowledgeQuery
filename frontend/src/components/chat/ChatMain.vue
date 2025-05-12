<template>
  <div class="main-content" :class="{ 'content-expanded': sidebarCollapsed }">
    <!-- 聊天区域 -->
    <div class="chat-content custom-scrollbar" ref="chatContentRef">
      <div v-if="chatMessages.length === 0" class="welcome">
        <div class="welcome-container">
          <div class="welcome-header">
            <h2>🤖 欢迎使用博物馆知识问答系统</h2>
            <p>有任何关于博物馆的问题，尽管问我吧！</p>
          </div>
          
          <!-- 提示卡片区域 - 现在放在搜索框上方 -->
          <div class="suggestion-container">
            <div class="suggestion-row">
              <div class="suggestion-card" @click="useExample('故宫的历史是怎样的？')">
                <span class="card-icon">🏛️</span>
                <span>故宫的历史是怎样的？</span>
              </div>
              <div class="suggestion-card" @click="useExample('中国古代青铜器有哪些特点？')">
                <span class="card-icon">🥉</span>
                <span>中国古代青铜器有哪些特点？</span>
              </div>
            </div>
            <div class="suggestion-row">
              <div class="suggestion-card" @click="useExample('敦煌莫高窟有哪些著名壁画？')">
                <span class="card-icon">🖼️</span>
                <span>敦煌莫高窟有哪些著名壁画？</span>
              </div>
              <div class="suggestion-card" @click="useExample('兵马俑的发现过程是怎样的？')">
                <span class="card-icon">⚔️</span>
                <span>兵马俑的发现过程是怎样的？</span>
              </div>
              <div class="suggestion-card" @click="useExample('中国古代丝绸之路的重要性？')">
                <span class="card-icon">🧵</span>
                <span>中国古代丝绸之路的重要性？</span>
              </div>
            </div>
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
</template>

<script setup>
import { ref, reactive, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '../../services/api'
import MarkdownIt from 'markdown-it'
import { Position } from '@element-plus/icons-vue'

// 初始化markdown-it解析器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
  highlight: function (str, lang) {
    return `<pre class="language-${lang}"><code>${str}</code></pre>`;
  }
});

const props = defineProps({
  currentSessionId: {
    type: String,
    default: null
  },
  sidebarCollapsed: {
    type: Boolean,
    default: false
  },
  sessionType: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['session-created', 'messages-updated'])

const loading = ref(false)
const userInput = ref('')
const chatContentRef = ref(null)
const inputRef = ref(null)
const centerInputRef = ref(null)
const chatMessages = reactive([])

// 使用示例问题
const useExample = (question) => {
  userInput.value = question
  nextTick(() => {
    if (centerInputRef.value && typeof centerInputRef.value.focus === 'function') {
      try {
        centerInputRef.value.focus()
      } catch (error) {
        console.error('聚焦输入框失败:', error)
      }
    }
  })
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

// 发送消息（流式响应版本）
const sendMessage = async () => {
  const message = userInput.value.trim()
  if (!message || loading.value) return

  // 如果没有会话ID，先创建会话
  if (!props.currentSessionId) {
    try {
      const response = await chatApi.createSession('新对话', props.sessionType)
      const newSession = response.data.data
      emit('session-created', newSession)
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
    const { url, options } = chatApi.sendStreamMessage(props.currentSessionId, message)
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
    
    // 通知父组件消息已更新
    emit('messages-updated', chatMessages)
    
    // 流式响应结束后，从服务器获取最新的会话消息
    if (props.currentSessionId) {
      try {
        const response = await chatApi.getSession(props.currentSessionId)
        if (response.data && response.data.data && response.data.data.messages) {
          // 用服务器返回的完整消息替换本地消息
          loadMessages(response.data.data.messages)
        }
      } catch (error) {
        console.error('获取会话消息失败:', error)
      }
    }
    
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

// 对外暴露加载消息的方法
const loadMessages = (messages) => {
  chatMessages.length = 0
  if (messages && messages.length) {
    messages.forEach(msg => {
      chatMessages.push({
        type: msg.is_user ? 'user' : 'system',
        content: msg.content
      })
    })
    nextTick(() => {
      scrollToBottom()
    })
  }
}

// 暴露方法给父组件
defineExpose({
  loadMessages,
  scrollToBottom
})

// 监听消息列表变化，自动滚动到底部
watch(() => chatMessages.length, () => {
  nextTick(() => {
    scrollToBottom()
  })
})
</script>

<style scoped>
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: #ffffff;
  margin: 16px 16px 16px 16px;
  border-radius: 16px; /* 更大的圆角 - 苹果风格 */
  box-shadow: 0 4px 20px rgba(0,0,0,0.05); /* 更柔和的阴影 - 苹果风格 */
  overflow: hidden;
  transition: all 0.3s ease;
}

.content-expanded {
  margin-left: 50px;
}

/* 欢迎页样式 */
.welcome {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 40px 20px; /* 更多顶部空间 - 苹果风格 */
}

.welcome-container {
  max-width: 1000px;
  width: 100%;
  text-align: center;
}

.welcome-header {
  margin-bottom: 32px; /* 增加间距 */
}

.welcome-header h2 {
  font-size: 36px; /* 从32px增加到36px */
  font-weight: 600;
  margin-bottom: 18px; /* 增加一些间距 */
  background: linear-gradient(135deg, #333333 0%, #666666 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.welcome-header p {
  font-size: 19px; /* 从17px增加到19px */
  color: #555555;
  font-weight: 400;
  letter-spacing: -0.2px;
}

/* 提示卡片容器 */
.suggestion-container {
  margin-bottom: 32px;
  width: 100%;
  max-width: 800px; /* 增加容器宽度 */
  margin-left: auto;
  margin-right: auto;
}

.suggestion-row {
  display: flex;
  justify-content: center;
  gap: 20px; /* 增加间距 */
  margin-bottom: 16px;
  flex-wrap: nowrap; /* 防止换行 */
}

/* 提示卡片样式 - 苹果风格 */
.suggestion-card {
  display: inline-flex;
  align-items: center;
  padding: 10px 20px; /* 从8px 16px增加到10px 20px */
  border: 1px solid #eaeaea;
  border-radius: 9999px;
  font-size: 16px; /* 从14px增加到16px */
  color: #333333;
  background-color: #fafafa;
  gap: 10px; /* 从8px增加到10px */
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none; /* 防止文本选择 */
  box-shadow: 0 1px 2px rgba(0,0,0,0.03); /* 极轻微阴影 - 苹果风格 */
  min-width: 240px; /* 从220px增加到240px */
  max-width: 350px; /* 从320px增加到350px */
  white-space: nowrap; /* 防止文本换行 */
  overflow: hidden; /* 隐藏溢出部分 */
  text-overflow: ellipsis; /* 显示省略号 */
}

/* 为第二行的卡片设置更宽的宽度，因为它们的内容可能更长 */
.suggestion-row:nth-child(2) .suggestion-card {
  min-width: 250px; /* 进一步增加宽度 */
  max-width: 350px;
}

.suggestion-card:hover {
  background-color: #f0f0f0;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

.suggestion-card:active {
  transform: translateY(0);
}

.card-icon {
  font-size: 18px; /* 从16px增加到18px */
}

.center-search {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}

.welcome-input {
  width: 100%;
  max-width: 800px;
  margin-bottom: 16px;
}

.welcome-input :deep(.el-textarea__inner) {
  font-size: 18px; /* 从16px增加到18px */
  padding: 18px; /* 从16px增加到18px */
  border-radius: 14px; /* 更大的圆角 - 苹果风格 */
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
  transition: all 0.3s ease;
  background-color: #ffffff;
  color: #333333;
  letter-spacing: -0.2px; /* 字母间距 - 苹果风格 */
}

.welcome-input :deep(.el-textarea__inner:focus) {
  border-color: #555555;
  box-shadow: 0 0 0 2px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.1);
}

.welcome-button {
  font-size: 18px; /* 从16px增加到18px */
  height: 50px; /* 从46px增加到50px */
  padding: 0 36px; /* 从0 32px增加到0 36px */
  border-radius: 9999px; /* 更圆的按钮 - 苹果风格 */
  background: #333333;
  border: none;
  transition: all 0.3s ease;
  letter-spacing: -0.2px;
  font-weight: 500;
}

.welcome-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  background-color: #444444;
}

.welcome-button:active {
  transform: translateY(1px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

/* 聊天区域样式 */
.chat-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  scroll-behavior: smooth;
  background-color: #ffffff;
}

.custom-scrollbar {
  position: relative;
  overflow-y: scroll;
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.15) transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.15);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.25);
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
  font-size: 28px; /* 从24px增加到28px */
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  position: relative;
}

.user-message-emoji {
  font-size: 28px; /* 从24px增加到28px */
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  position: relative;
  margin-right: 80px;
}

.user-message {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.user-content {
  background-color: #333333;
  color: white;
  border-radius: 18px 18px 4px 18px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1); /* 更细腻的阴影 */
}

.ai-message {
  align-self: flex-start;
}

.ai-content {
  background-color: #f5f5f5;
  color: #333333;
  border-radius: 18px 18px 18px 4px;
  border: 1px solid #e8e8e8;
}

.message-content {
  border-radius: 14px; /* 增大圆角 */
  padding: 14px 20px;
  position: relative;
  max-width: calc(100% - 40px);
}

.message-text {
  word-break: break-word;
  line-height: 1.6; /* 从1.5增加到1.6 */
  letter-spacing: -0.2px; /* 苹果风格字间距 */
  font-size: 16px; /* 添加字体大小 */
}

/* 输入区域样式 */
.chat-input-area {
  padding: 20px;
  border-top: 1px solid #f0f0f0; /* 更浅的边框 */
  background-color: #ffffff;
}

.chat-input-area :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 16px; /* 从14px增加到16px */
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
  background-color: #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  font-size: 17px; /* 从15px增加到17px */
  letter-spacing: -0.2px;
}

.input-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.input-actions .el-button {
  border-radius: 9999px; /* 圆形按钮 - 苹果风格 */
  padding: 12px 28px; /* 从10px 24px增加到12px 28px */
  background-color: #333333;
  border-color: #333333;
  font-weight: 500;
  letter-spacing: -0.2px;
  font-size: 16px; /* 添加字体大小 */
}

/* Markdown样式 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif; /* 苹果字体 */
  line-height: 1.6;
  color: #333333;
  letter-spacing: -0.2px;
  font-size: 16px; /* 添加基本字体大小 */
}

/* 保留其余样式，增加苹果风格的字体和细节 */
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
  color: #222222;
  letter-spacing: -0.3px;
}

/* 统一element-plus按钮颜色 */
:deep(.el-button--primary) {
  background-color: #333333;
  border-color: #333333;
  letter-spacing: -0.2px;
  font-weight: 500;
}

:deep(.el-button--primary:hover) {
  background-color: #444444;
  border-color: #444444;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

:deep(.el-button--primary:focus) {
  background-color: #444444;
  border-color: #444444;
}

:deep(.el-button--primary.is-disabled) {
  background-color: #a0a0a0;
  border-color: #a0a0a0;
}
</style>
