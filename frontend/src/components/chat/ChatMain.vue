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
            <el-input v-model="userInput" placeholder="请输入您想了解的博物馆知识..." :disabled="loading" type="textarea" :rows="3"
              resize="none" @keydown.enter.prevent="handleEnterKeyPress" ref="centerInputRef" class="welcome-input" />

            <!-- 添加按钮组：模型选择器和开始提问按钮 -->
            <div class="welcome-button-group">
              <div class="welcome-model-select-container">
                <el-select v-model="currentModel" placeholder="选择AI模型" size="large" :disabled="loading"
                  class="welcome-model-select">
                  <el-option v-for="model in availableModels" :key="model.value" :label="model.label"
                    :value="model.value" />
                </el-select>
              </div>

              <el-button type="primary" size="large" :disabled="loading || !userInput.trim()" @click="sendMessage"
                class="welcome-button">
                开始提问 <el-icon class="el-icon--right">
                  <Position />
                </el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="message-list">
        <div v-for="(message, index) in chatMessages" :key="index"
          :class="['message', message.type === 'user' ? 'user-message' : 'ai-message']">
          <!-- AI消息 -->
          <template v-if="message.type !== 'user'">
            <div class="message-emoji">🤖</div>
            <div class="message-content ai-content">
              <div v-if="loading && index === chatMessages.length - 1 && message.content === ''"
                class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div v-else-if="loading && index === chatMessages.length - 1" class="message-text markdown-body">
                <!-- 使用更高级的流式输出指示器 -->
                <div class="streaming-indicator">
                  <div class="streaming-badge">
                    <span class="streaming-dot"></span>
                    AI正在思考
                  </div>
                  <!-- 添加终止按钮 -->
                  <el-button 
                    class="stop-button" 
                    type="danger" 
                    size="small" 
                    @click="stopGenerating"
                    :icon="CircleClose">
                    终止回答
                  </el-button>
                </div>
                <v-md-preview :text="message.content" />
              </div>
              <div v-else class="message-text markdown-body">
                <v-md-preview :text="message.content" />
                <!-- 添加复制按钮 -->
                <div class="message-actions">
                  <el-button 
                    class="copy-button" 
                    type="info" 
                    size="small" 
                    @click="copyMessage(message.content)"
                    :icon="Document">
                    复制回答
                  </el-button>
                </div>
              </div>
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
    </div>

    <!-- 输入区域 - 只在有消息时显示 -->
    <div class="chat-input-area" v-if="chatMessages.length > 0">
      <!-- 添加模型选择器 -->
      <div class="model-selector">
        <span class="model-label">选择模型：</span>
        <el-select v-model="currentModel" placeholder="选择AI模型" size="small" :disabled="loading">
          <el-option v-for="model in availableModels" :key="model.value" :label="model.label" :value="model.value" />
        </el-select>
      </div>

      <el-input v-model="userInput" placeholder="请输入您想了解的博物馆知识..." :disabled="loading" type="textarea" :rows="2"
        resize="none" @keydown.enter.prevent="handleEnterKeyPress" ref="inputRef" />
      <div class="input-actions">
        <el-button type="primary" :disabled="loading || !userInput.trim()" @click="sendMessage">
          发送 <el-icon class="el-icon--right">
            <Position />
          </el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '../../services/api'
// 修改导入，添加更多图标
import { Position, Document, CircleClose } from '@element-plus/icons-vue'

// 导入 VMdEditor 和 VMdPreview
import VMdPreview from '@kangc/v-md-editor/lib/preview';
import '@kangc/v-md-editor/lib/style/base-editor.css';
import githubTheme from '@kangc/v-md-editor/lib/theme/github.js';
import '@kangc/v-md-editor/lib/theme/style/github.css';

// 导入代码高亮
import hljs from 'highlight.js';
import 'highlight.js/styles/github.css';

// 配置 VMdPreview
VMdPreview.use(githubTheme, {
  Hljs: hljs,
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
// 添加 abortController 用于终止请求
const abortController = ref(null)

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

// 滚动到底部
const scrollToBottom = () => {
  if (chatContentRef.value) {
    chatContentRef.value.scrollTop = chatContentRef.value.scrollHeight
  }
}

// 处理回车键
const handleEnterKeyPress = (e) => {
  // 如果按下了Shift键+回车，允许换行
  if (e.shiftKey) {
    return;
  }

  // 否则发送消息
  sendMessage();
}

// 添加一个缓冲区状态，用于临时存储流式响应内容
const streamBuffer = ref('')

// 添加可用模型列表
const availableModels = [
  { label: 'Gemini 2.5 Flash', value: 'gemini-2.5-flash-preview-04-17-nothink' },
  { label: 'DeepSeek R1', value: 'DeepSeek-R1' },
  { label: 'Qwen 3.0 (30B)', value: 'Qwen/Qwen3-30B-A3B' },
  { label: 'gpt-4o-search-preview', value: 'gpt-4o-search-preview' },
  { label: 'moonshotai', value: 'moonshotai/Moonlight-16B-A3B-Instruct' },
  { label: 'Doubao-1.5-thinking-pro', value: 'Doubao-1.5-thinking-pro' }
]

// 当前选择的模型
const currentModel = ref('gemini-2.5-flash-preview-04-17-nothink')

// 复制消息内容
const copyMessage = (content) => {
  if (!content) return
  
  navigator.clipboard.writeText(content)
    .then(() => {
      ElMessage({
        message: '已复制到剪贴板',
        type: 'success',
        duration: 2000
      })
    })
    .catch(err => {
      console.error('复制失败:', err)
      ElMessage.error('复制失败，请手动复制')
    })
}

// 终止AI回答生成
const stopGenerating = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
    console.log('已终止AI回答生成')
    loading.value = false
  }
}

// 发送消息（流式响应版本）- 修复流式输出问题
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

  // 先插入空字符串用于显示打字指示器
  chatMessages.push({
    type: 'system',
    content: ''
  })

  try {
    console.log('准备发送流式请求...')
    // 准备流式请求，传递选择的模型
    const { url, options } = chatApi.sendStreamMessage(props.currentSessionId, message, currentModel.value)
    console.log('请求URL:', url)

    // 创建 AbortController 用于终止请求
    abortController.value = new AbortController()
    options.signal = abortController.value.signal

    const response = await fetch(url, options)
    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`)
    }

    console.log('成功建立流式连接')

    // 使用更可靠的流处理方式
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        console.log('流式响应结束')
        break
      }

      // 解码二进制数据为文本
      const chunk = decoder.decode(value, { stream: true })
      console.log('收到流式数据片段:', chunk)
      buffer += chunk

      // 处理服务器发送的事件格式 (Server-Sent Events)
      // 格式为 "data: 内容\n\n"
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || '' // 保留最后一个可能不完整的部分

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const content = line.substring(6) // 去除 "data: " 前缀

          // 处理特殊标记
          if (content === '[START]') {
            console.log('收到流开始标记')
            continue
          } else if (content === '[DONE]') {
            console.log('收到流结束标记')
            continue
          }

          console.log('处理内容:', content)
          aiContent += content

          // 更新UI
          if (aiMessageIndex < chatMessages.length) {
            chatMessages[aiMessageIndex].content = aiContent
            // 触发DOM更新并滚动
            await nextTick()
            scrollToBottom()
          }
        }
      }
    }

    // 确保处理buffer中剩余的内容
    if (buffer.startsWith('data: ')) {
      const content = buffer.substring(6)
      if (content && content !== '[DONE]') {
        aiContent += content
        if (aiMessageIndex < chatMessages.length) {
          chatMessages[aiMessageIndex].content = aiContent
        }
      }
    }

    console.log('流式响应处理完成, 最终内容长度:', aiContent.length)

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
    // 判断是否是用户主动终止
    if (error.name === 'AbortError') {
      console.log('用户取消了请求')
      // 保留已生成的内容
      if (aiMessageIndex < chatMessages.length && aiContent) {
        chatMessages[aiMessageIndex].content = aiContent + '\n\n[用户已终止回答]'
      }
    } else {
      console.error('流式消息接收失败:', error)
      if (aiMessageIndex < chatMessages.length) {
        chatMessages[aiMessageIndex].content = '消息发送失败，请稍后再试。错误: ' + error.message
      }
      ElMessage.error('发送消息失败: ' + error.message)
    }
  } finally {
    loading.value = false
    abortController.value = null
    nextTick(() => {
      scrollToBottom()
    })
  }
}

// 改进的Markdown流式处理函数
const processMarkdownStreaming = (text) => {
  if (!text) return '';

  // 输入文本拆分为行
  const lines = text.split('\n');

  // 处理未完成的标题
  const processedLines = lines.map((line, index, array) => {
    // 是否为最后一行
    const isLastLine = index === array.length - 1;

    // 处理标题格式（# 开头的行）
    if (line.match(/^#{1,6}\s+/)) {
      // 如果是最后一行且不以换行符结束，可能是未完成的标题
      if (isLastLine && text[text.length - 1] !== '\n') {
        // 暂时处理为普通文本，但保留前缀
        return line;
      }
    }

    // 处理代码块（```开头的行）
    if (line.trim().startsWith('```')) {
      const codeBlockStart = line.trim();

      // 找出后续是否有对应的代码块结束标记
      let hasClosing = false;
      for (let i = index + 1; i < array.length; i++) {
        if (array[i].trim() === '```') {
          hasClosing = true;
          break;
        }
      }

      // 如果没有结束标记且当前是最后一行，添加虚拟结束标记
      if (!hasClosing && isLastLine) {
        return line + '\n\n```\n<!-- 临时代码块结束标记 -->';
      }
    }

    // 处理无序列表项（可能未完成）
    if (line.match(/^[*\-+]\s+/)) {
      // 确保列表项格式正确
      return line;
    }

    // 处理有序列表项（可能未完成）
    if (line.match(/^\d+\.\s+/)) {
      // 确保列表项格式正确
      return line;
    }

    return line;
  });

  return processedLines.join('\n');
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
  margin: 16px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative; /* 保留相对定位 */
}

.content-expanded {
  margin-left: 16px; /* 当侧边栏隐藏时，调整左边距 */
}

/* 欢迎页样式 */
.welcome {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  padding: 40px 20px;
  /* 更多顶部空间 - 苹果风格 */
}

.welcome-container {
  max-width: 1000px;
  width: 100%;
  text-align: center;
}

.welcome-header {
  margin-bottom: 32px;
  /* 增加间距 */
}

.welcome-header h2 {
  font-size: 36px;
  /* 从32px增加到36px */
  font-weight: 600;
  margin-bottom: 18px;
  /* 增加一些间距 */
  background: linear-gradient(135deg, #333333 0%, #666666 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.5px;
}

.welcome-header p {
  font-size: 19px;
  /* 从17px增加到19px */
  color: #555555;
  font-weight: 400;
  letter-spacing: -0.2px;
}

/* 提示卡片容器 */
.suggestion-container {
  margin-bottom: 32px;
  width: 100%;
  max-width: 800px;
  /* 增加容器宽度 */
  margin-left: auto;
  margin-right: auto;
}

.suggestion-row {
  display: flex;
  justify-content: center;
  gap: 20px;
  /* 增加间距 */
  margin-bottom: 16px;
  flex-wrap: nowrap;
  /* 防止换行 */
}

/* 提示卡片样式 - 苹果风格 */
.suggestion-card {
  display: inline-flex;
  align-items: center;
  padding: 10px 20px;
  /* 从8px 16px增加到10px 20px */
  border: 1px solid #eaeaea;
  border-radius: 9999px;
  font-size: 16px;
  /* 从14px增加到16px */
  color: #333333;
  background-color: #fafafa;
  gap: 10px;
  /* 从8px增加到10px */
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  /* 防止文本选择 */
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
  /* 极轻微阴影 - 苹果风格 */
  min-width: 240px;
  /* 从220px增加到240px */
  max-width: 350px;
  /* 从320px增加到350px */
  white-space: nowrap;
  /* 防止文本换行 */
  overflow: hidden;
  /* 隐藏溢出部分 */
  text-overflow: ellipsis;
  /* 显示省略号 */
}

/* 为第二行的卡片设置更宽的宽度，因为它们的内容可能更长 */
.suggestion-row:nth-child(2) .suggestion-card {
  min-width: 250px;
  /* 进一步增加宽度 */
  max-width: 350px;
}

.suggestion-card:hover {
  background-color: #f0f0f0;
  transform: translateY(-1px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

.suggestion-card:active {
  transform: translateY(0);
}

.card-icon {
  font-size: 18px;
  /* 从16px增加到18px */
}

.center-search {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40px;
}

/* 添加按钮组样式 */
.welcome-button-group {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  width: 100%;
  max-width: 800px;
  margin-top: 16px;
}

.welcome-model-select-container {
  flex: 0 0 auto;
}

.welcome-model-select {
  width: 240px;
}

.welcome-model-select :deep(.el-input__wrapper) {
  border-radius: 9999px;
  /* 与按钮相同的圆角 */
  background-color: #f8f8f8;
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  padding: 4px 16px;
  height: 50px;
  /* 与按钮高度相同 */
  transition: all 0.3s;
}

.welcome-model-select :deep(.el-input__wrapper:hover) {
  border-color: #b3b3b3;
  background-color: #ffffff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.welcome-model-select :deep(.el-input__wrapper.is-focus) {
  border-color: #555555;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
  background-color: #ffffff;
}

.welcome-model-select :deep(.el-input__inner) {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.welcome-input {
  width: 100%;
  max-width: 800px;
  margin-bottom: 16px;
}

.welcome-input :deep(.el-textarea__inner) {
  font-size: 18px;
  /* 从16px增加到18px */
  padding: 18px;
  /* 从16px增加到18px */
  border-radius: 14px;
  /* 更大的圆角 - 苹果风格 */
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  background-color: #ffffff;
  color: #333333;
  letter-spacing: -0.2px;
  /* 字母间距 - 苹果风格 */
}

.welcome-input :deep(.el-textarea__inner:focus) {
  border-color: #555555;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.1);
}

.welcome-button {
  font-size: 18px;
  /* 从16px增加到18px */
  height: 50px;
  /* 从46px增加到50px */
  padding: 0 36px;
  /* 从0 32px增加到0 36px */
  border-radius: 9999px;
  /* 更圆的按钮 - 苹果风格 */
  background: #333333;
  border: none;
  transition: all 0.3s ease;
  letter-spacing: -0.2px;
  font-weight: 500;
  flex: 0 0 auto;
}

.welcome-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  background-color: #444444;
}

.welcome-button:active {
  transform: translateY(1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  margin-left: 5%;
  margin-right: 5%;
  gap: 20px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 90%;
}

.message-emoji {
  font-size: 28px;
  /* 从24px增加到28px */
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  position: relative;
}

.user-message-emoji {
  font-size: 28px;
  /* 从24px增加到28px */
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
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  /* 更细腻的阴影 */
}

.ai-message {
  align-self: flex-start;
}

.ai-content {
  background-color: #f5f5f5;
  color: #333333;
  border-radius: 18px 18px 18px 4px;
  border: 1px solid #e8e8e8;
  min-width: 500px;
}

.message-content {
  border-radius: 14px;
  /* 增大圆角 */
  padding: 14px 20px;
  position: relative;
  max-width: calc(100% - 40px);
}

.message-text {
  word-break: break-word;
  font-size: 16px;
  /* 从14px增加到16px */
  line-height: 1.6;
  /* 从1.5增加到1.6 */
  letter-spacing: -0.2px;
  /* 苹果风格字间距 */
  font-size: 16px;
  /* 添加字体大小 */
}

/* Skeleton动画样式 */
:deep(.el-skeleton) {
  width: 100%;
}

:deep(.el-skeleton__item) {
  background: linear-gradient(90deg, #f2f2f2 25%, #e6e6e6 37%, #f2f2f2 63%);
  background-size: 400% 100%;
}

:deep(.el-skeleton.is-animated .el-skeleton__item) {
  animation-duration: 1.8s;
  animation-timing-function: ease;
}

/* 输入区域样式 */
.chat-input-area {
  padding: 20px;
  border-top: 1px solid #f0f0f0;
  /* 更浅的边框 */
  background-color: #ffffff;
}

.chat-input-area :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 16px;
  /* 从14px增加到16px */
  border: 1px solid #e0e0e0;
  transition: all 0.3s ease;
  background-color: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  font-size: 17px;
  /* 从15px增加到17px */
  letter-spacing: -0.2px;
}

.input-actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.input-actions .el-button {
  border-radius: 9999px;
  /* 圆形按钮 - 苹果风格 */
  padding: 12px 28px;
  /* 从10px 24px增加到12px 28px */
  background-color: #333333;
  border-color: #333333;
  font-weight: 500;
  letter-spacing: -0.2px;
  font-size: 16px;
  /* 添加字体大小 */
}

/* Markdown样式 */
.markdown-body {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
  /* 苹果字体 */
  line-height: 1.6;
  color: #333333;
  letter-spacing: -0.2px;
  font-size: 16px;
  /* 添加基本字体大小 */
}

/* 修改 Markdown 样式部分，适配 VMdPreview */
.message-text :deep(.v-md-editor) {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
}

.message-text :deep(.v-md-editor__preview) {
  padding: 0 !important;
  background-color: transparent !important;
}

/* 保留原有的特殊样式，但调整为适配 VMdPreview 的选择器 */
.message-text :deep(.v-md-editor__preview h1),
.message-text :deep(.v-md-editor__preview h2),
.message-text :deep(.v-md-editor__preview h3),
.message-text :deep(.v-md-editor__preview h4),
.message-text :deep(.v-md-editor__preview h5),
.message-text :deep(.v-md-editor__preview h6) {
  margin-top: 24px;
  margin-bottom: 16px;
  font-weight: 600;
  line-height: 1.25;
  color: #222222;
  letter-spacing: -0.3px;
  /* 确保即使标题未完成也能正确显示 */
  display: block;
}

/* 确保流式输出时段落正确显示 */
.message-text :deep(.v-md-editor__preview p) {
  margin-bottom: 16px;
  line-height: 1.6;
}

/* 优化代码块在流式输出时的显示 */
.message-text :deep(.v-md-editor__preview pre) {
  margin-bottom: 16px;
  position: relative;
  /* 确保代码块即使未闭合也能正确显示 */
  display: block;
}

.message-text :deep(.v-md-editor__preview pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  white-space: pre;
}

.message-text :deep(.v-md-editor__preview table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

.message-text :deep(.v-md-editor__preview table th),
.message-text :deep(.v-md-editor__preview table td) {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
  text-align: left;
}

.message-text :deep(.v-md-editor__preview table th) {
  background-color: #f6f8fa;
  font-weight: 600;
}

.message-text :deep(.v-md-editor__preview blockquote) {
  margin: 16px 0;
  padding: 0 16px;
  color: #57606a;
  border-left: 4px solid #d0d7de;
}

.message-text :deep(.math-block) {
  display: block;
  margin: 16px 0;
  text-align: center;
  overflow-x: auto;
}

.message-text :deep(.math-inline) {
  display: inline;
}

/* 保留原有的Skeleton动画样式 */
:deep(.el-skeleton) {
  width: 100%;
}

:deep(.el-skeleton__item) {
  background: linear-gradient(90deg, #f2f2f2 25%, #e6e6e6 37%, #f2f2f2 63%);
  background-size: 400% 100%;
}

:deep(.el-skeleton.is-animated .el-skeleton__item) {
  animation-duration: 1.8s;
  animation-timing-function: ease;
}

/* 流式输出时的专业指示器样式 */
.streaming-indicator {
  position: relative;
  margin-bottom: 8px;
}

.streaming-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background-color: #f0f7ff;
  color: #1890ff;
  border-radius: 12px;
  font-size: 12px;
  margin-bottom: 8px;
  animation: pulse 2s infinite;
  border: 1px solid rgba(24, 144, 255, 0.2);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.streaming-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #1890ff;
  display: inline-block;
  animation: blink 1.4s infinite ease-in-out;
}

@keyframes blink {

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.4;
  }
}

/* 改进的打字指示器 */
.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 24px;
  padding: 8px 12px;
  background-color: #f5f5f5;
  border-radius: 12px;
  margin-top: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #666;
  display: inline-block;
  opacity: 0.4;
}

.typing-indicator span:nth-child(1) {
  animation: typingAnimation 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation: typingAnimation 1.4s infinite ease-in-out 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation: typingAnimation 1.4s infinite ease-in-out 0.4s;
}

@keyframes typingAnimation {

  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.4;
  }

  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

/* 专业的Markdown流式渲染样式 */
.message-text :deep(.v-md-editor__preview h1),
.message-text :deep(.v-md-editor__preview h2),
.message-text :deep(.v-md-editor__preview h3),
.message-text :deep(.v-md-editor__preview h4),
.message-text :deep(.v-md-editor__preview h5),
.message-text :deep(.v-md-editor__preview h6) {
  position: relative;
  margin-top: 24px;
  margin-bottom: 16px;
  line-height: 1.25;
  font-weight: 600;
  border-bottom: none;
}

.message-text :deep(.v-md-editor__preview h1) {
  font-size: 2em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
}

.message-text :deep(.v-md-editor__preview h2) {
  font-size: 1.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
}

.message-text :deep(.v-md-editor__preview h3) {
  font-size: 1.25em;
}

.message-text :deep(.v-md-editor__preview ul),
.message-text :deep(.v-md-editor__preview ol) {
  padding-left: 2em;
  margin-bottom: 16px;
}

/* 添加消息操作按钮样式 */
.message-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 12px;
  gap: 8px;
}

.copy-button {
  border-radius: 6px;
  font-size: 13px;
  padding: 6px 12px;
  background-color: #f5f5f5;
  color: #606266;
}

.model-selector :deep(.el-select) {
  width: 200px;
}

/* 终止按钮样式 */
.stop-button {
  border-radius: 6px;
  font-size: 13px;
  padding: 6px 12px;
  background-color: #fff0f0;
  color: #f56c6c;
  border: 1px solid #fbc4c4;
  margin-left: 10px;
  transition: all 0.3s;
}

.stop-button:hover {
  background-color: #fef0f0;
  color: #f56c6c;
  border-color: #f56c6c;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

/* 响应式设计 - 适配不同设备 */
@media (max-width: 1200px) {
  .welcome-container {
    max-width: 90%;
  }
  
  .suggestion-container {
    max-width: 90%;
  }
  
  .center-search,
  .welcome-input,
  .welcome-button-group {
    max-width: 90%;
  }
}

@media (max-width: 768px) {
  .content-expanded {
    margin-left: 16px;
    width: calc(100% - 32px); /* 确保在小屏幕上填满宽度 */
  }
  
  .message-actions {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .main-content {
    margin: 8px;
    border-radius: 12px;
  }
  
  .chat-content {
    padding: 16px;
  }
  
  .message-list {
    margin-left: 0;
    margin-right: 0;
  }
  
  .welcome-header h2 {
    font-size: 24px;
  }
  
  .message {
    max-width: 100%;
  }
  
  .user-message-emoji, 
  .message-emoji {
    font-size: 24px;
  }
  
  .chat-input-area {
    padding: 12px;
  }
  
  .input-actions .el-button {
    padding: 8px 20px;
    font-size: 14px;
  }
  
  .welcome-button {
    height: 44px;
    font-size: 16px;
    padding: 0 24px;
  }
  
  .copy-button, 
  .stop-button {
    padding: 4px 8px;
    font-size: 12px;
  }
}
</style>
