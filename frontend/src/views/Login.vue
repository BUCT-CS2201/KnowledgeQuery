<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧信息部分 -->
      <div class="login-info">
        <div class="login-info-content">
          <div class="img-box">
            <img src="../assets/logo.png" alt="博物馆logo" />
          </div>
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
            <a href="javascript:void(0)" class="forgot-password" @click="goToForgotPassword">忘记密码？</a>
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
            <span>没有账号?</span>
            <router-link to="/register" class="register-link">立即注册</router-link>
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

const goToForgotPassword = () => {
  router.push('/forgot-password')
}
</script>

<style scoped>
.login-page {
  position: fixed;
  left: 0;
  top: 0;
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  min-width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background-image: url('../assets/background.png');
  /* background: linear-gradient(135deg, #eaeaea 0%, #ffffff 100%), url('../assets/background.png'); */
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  overflow: hidden;
  z-index: 1000;
}

.login-container {
  max-width: 700px;
  width: 90vw;
  height: 480px;
  display: flex;
  background-color: rgba(255, 255, 255, 0.92);
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
  overflow: hidden;
  position: relative;
  z-index: 1;
  margin: 0 auto;
}

.login-info {
  width: 60%;
  min-width: 220px;
  background: rgba(2, 2, 2, 0.675); /* 黑色但更透明 */
  color: #fff;
  padding: 32px 18px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  position: relative;
  overflow: hidden;

  backdrop-filter: blur(12px) saturate(1.5);
  -webkit-backdrop-filter: blur(12px) saturate(1.5);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  border-radius: 12px;
}

.login-info::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
  animation: rotate 20s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.img-box {
  width: 90px;
  height: 90px;
  margin: 0 auto 18px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.18);
  animation: imgBoxFadeIn 1s ease-out 0.3s both;
}

@keyframes imgBoxFadeIn {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.img-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.img-box:hover img {
  transform: scale(1.1);
}

.system-name {
  font-size: 22px;
  font-family: 'SimSun', '宋体', serif;
  font-weight: bold;
  margin-bottom: 12px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.13);
  animation: textFadeIn 1s ease-out 0.5s both;
}

.system-desc {
  font-size: 14px;
  opacity: 0.92; 
  text-shadow: 1px 1px 2px rgba(36, 35, 35, 0.078);
  animation: textFadeIn 1s ease-out 0.7s both;
  font-family: 'SimSun', '宋体', serif;
  text-align: center;
}

@keyframes textFadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-form-container {
  width: 100%;
  padding: 30px 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(20px) saturate(1.8);
  -webkit-backdrop-filter: blur(20px) saturate(1.8);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.10);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 18px;
  animation: reloadA 1s ease-out forwards;
  opacity: 0;
  animation-delay: 0.2s;
  transition: all 0.3s ease-in-out;
}

@keyframes reloadA {
  from {
    transform: translateY(80px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.login-form-header {
  margin-bottom: 32px;
  text-align: center;
}

.login-form-header h2 {
  font-size: 25px;
  color: #222;
  font-family: 'SimSun', '宋体', serif;
  font-weight: 600;
  letter-spacing: 2px;
  position: relative;
  display: inline-block;
}

.login-form-header h2::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 38px;
  height: 2.5px;
  background: #222;
  border-radius: 2px;
}

.login-form {
  width: 100%;
  padding: 0;
  border-radius: 18px;
  box-sizing: border-box;
  transition: all 0.3s ease-in-out;
}

:deep(.el-input__wrapper) {
  background-color: transparent !important;
  border-radius: 18px;
  box-shadow: 0 0 5px rgba(0, 0, 0, 0.08);
  border: 1.5px solid #e0e0e0;
  color: #222;
  transition: all 0.3s cubic-bezier(.4,2,.6,1);
}

:deep(.el-input__inner) {
  height: 42px;
  font-size: 15px;
  background: transparent !important;
  color: #222;
}

.form-options {
  display: flex;
  font-size: 14px;
  font-family: 'SimSun', '宋体', serif;
  justify-content: space-between;
  margin-bottom: 18px;
  align-items: center;
}

.forgot-password {
  color: #888;
  text-decoration: none;
  transition: all 0.3s;
  position: relative;
  font-size: 13px;
  font-family: 'SimSun', '宋体', serif;
}

.forgot-password:hover {
  color: #111;
}

.login-button {
  width: 100%;
  height: 48px;
  border-radius: 50px;
  background: #111;
  border: none;
  font-size: 16px;
  font-family: 'SimSun', '宋体', serif;
  font-weight: 600;
  letter-spacing: 1px;
  margin-bottom: 18px;
  cursor: pointer;
  transition: 0.3s;
  color: #fff;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.10);
  animation: reloadA 1.2s ease-out forwards;
  opacity: 0;
  animation-delay: 0.4s;
}

.login-button:hover {
  background: #444;
  color: #fff;
}

.form-footer {
  margin-top: 18px;
  text-align: center;
  font-size: 15px;
  font-family: 'SimSun', '黑体', serif;
  color: #888;
}

.register-link {
  color: #3a3939;
  text-decoration: none;
  margin-left: 2px;
  transition: all 0.3s;
  position: relative;
  font-family: 'SimSun', '宋体', serif;
}

.register-link:hover {
  color: #000;
}

@media (max-width: 900px) {
  .login-container {
    width: 98vw;
    min-width: 320px;
    flex-direction: column;
    height: auto;
  }
  .login-info, .login-form-container {
    width: 100%;
    min-width: 0;
    border-radius: 0;
    padding: 24px 10vw;
  }
  .login-form-container {
    border-left: none;
    border-top: 1.5px solid rgba(200,200,200,0.08);
  }
}
</style>
