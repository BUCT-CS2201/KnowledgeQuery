<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧信息部分 -->
      <div class="login-info">
        <div class="login-info-content">
          <h1 class="system-name">博物馆知识问答系统</h1>
          <p class="system-desc">探索历史文化，发现艺术魅力</p>
        </div>
      </div>
      
      <!-- 右侧登录表单 -->
      <div class="login-form-container">
        <div class="login-form-header">
          <h2>账号登录</h2>
        </div>
        
        <el-form 
          ref="loginFormRef" 
          :model="loginForm" 
          :rules="rules" 
          class="login-form">
          
          <el-form-item prop="phone_number">
            <el-input 
              v-model="loginForm.phone_number" 
              placeholder="请输入手机号"
              prefix-icon="Phone" />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="loginForm.password" 
              type="password" 
              placeholder="请输入密码"
              prefix-icon="Lock" 
              show-password />
          </el-form-item>
          
          <div class="form-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <a href="javascript:void(0)" class="forgot-password">忘记密码？</a>
          </div>
          
          <el-form-item>
            <el-button 
              type="primary" 
              :loading="loading" 
              @click="handleLogin" 
              class="login-button">
              登录
            </el-button>
          </el-form-item>
          
          <div class="form-footer">
            <span>没有账号？</span>
            <router-link to="/register">立即注册</router-link>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { accountApi } from '../services/api'

const router = useRouter()
const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  phone_number: '',
  password: ''
})

const rules = reactive({
  phone_number: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号码', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await accountApi.login(loginForm)
        
        if (response.data.code === 200) {
          // 保存登录凭证
          const userData = response.data.data
          localStorage.setItem('token', userData.access_token)
          localStorage.setItem('user', JSON.stringify({
            userId: userData.user_id,
            name: userData.name,
            phone: userData.phone_number
          }))
          
          ElMessage.success('登录成功')
          // 跳转到问答界面
          router.push('/chat')
        } else {
          ElMessage.error(response.data.message || '登录失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '登录出错，请稍后再试')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f5f7fa;
  position: fixed
}

.login-container {
  width: 800px;
  height: 500px;
  display: flex;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  overflow: hidden;
}

/* 左侧信息样式 */
.login-info {
  flex: 1;
  background-color: #1890ff;
  color: white;
  padding: 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.system-name {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 16px;
}

.system-desc {
  font-size: 16px;
  opacity: 0.9;
}

/* 右侧表单样式 */
.login-form-container {
  width: 400px;
  padding: 30px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-form-header {
  margin-bottom: 30px;
  text-align: center;
}

.login-form-header h2 {
  font-size: 20px;
  color: #333;
}

.login-form {
  width: 100%;
}

.form-options {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.forgot-password {
  color: #1890ff;
  text-decoration: none;
}

.login-button {
  width: 100%;
}

.form-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

.form-footer a {
  color: #1890ff;
  text-decoration: none;
  margin-left: 4px;
}

/* 适配较小屏幕 */
@media (max-width: 768px) {
  .login-container {
    width: 95%;
    flex-direction: column;
    height: auto;
  }
  
  .login-form-container {
    width: 100%;
  }
}
</style>
