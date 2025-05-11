<template>
  <div class="register-page">
    <div class="register-container">
      <!-- 左侧信息部分 -->
      <div class="register-info">
        <div class="register-info-content">
          <div class="img-box">
            <img src="../assets/logo.png" alt="博物馆logo" />
          </div>
          <h1 class="system-name">博物馆知识问答系统</h1>
          <p class="system-desc">注册账号，开启知识探索之旅</p>
        </div>
      </div>
      
      <!-- 右侧注册表单 -->
      <div class="register-form-container">
        <div class="register-form-header">
          <h2>账号注册</h2>
        </div>
        
        <el-form 
          ref="registerFormRef" 
          :model="registerForm" 
          :rules="rules"
          class="register-form">
          
          <el-form-item prop="name">
            <el-input 
              v-model="registerForm.name" 
              placeholder="请输入姓名" />
          </el-form-item>
          
          <el-form-item prop="phone_number">
            <el-input 
              v-model="registerForm.phone_number" 
              placeholder="请输入手机号" />
          </el-form-item>
          
          <el-form-item prop="id_number">
            <el-input 
              v-model="registerForm.id_number" 
              placeholder="请输入身份证号" />
          </el-form-item>
          
          <el-form-item prop="password">
            <el-input 
              v-model="registerForm.password" 
              type="password" 
              placeholder="请输入密码"
              show-password />
          </el-form-item>
          
          <el-form-item prop="confirmPassword">
            <el-input 
              v-model="registerForm.confirmPassword" 
              type="password" 
              placeholder="请再次输入密码"
              show-password />
          </el-form-item>
          
          <el-form-item>
            <div class="agreement">
              <el-checkbox v-model="agreement">我已阅读并同意</el-checkbox>
              <span>我们的</span>
              <router-link to="/user-agreement" class="agreement-link">用户协议</router-link>
              <span>与</span>
              <router-link to="/privacy-policy" class="agreement-link">隐私政策</router-link>
            </div>
          </el-form-item>
          
          <el-form-item>
            <el-button 
              type="primary" 
              :loading="loading" 
              @click="handleRegister" 
              :disabled="!agreement"
              class="register-button">
              注册
            </el-button>
          </el-form-item>
          
          <div class="form-footer">
            <span>已有账号？</span>
            <router-link to="/login" class="register-link">返回登录</router-link>
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
const registerFormRef = ref(null)
const loading = ref(false)
const agreement = ref(false)

const registerForm = reactive({
  name: '',
  phone_number: '',
  id_number: '',
  password: '',
  confirmPassword: ''
})

// 校验密码是否一致的方法
const validatePass = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = reactive({
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 20, message: '姓名长度在2到20个字符之间', trigger: 'blur' }
  ],
  phone_number: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号码', trigger: 'blur' }
  ],
  id_number: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { pattern: /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/, message: '请输入有效的身份证号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ]
})

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      if (!agreement.value) {
        ElMessage.warning('请阅读并同意用户协议和隐私政策')
        return
      }
      
      loading.value = true
      
      // 创建提交对象，不包含确认密码
      const submitData = {
        name: registerForm.name,
        phone_number: registerForm.phone_number,
        id_number: registerForm.id_number,
        password: registerForm.password
      }
      
      try {
        const response = await accountApi.register(submitData)
        
        if (response.data.code === 200) {
          ElMessage.success('注册成功，请登录')
          router.push('/login')
        } else {
          ElMessage.error(response.data.message || '注册失败')
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '注册出错，请稍后再试')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-page {
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
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  overflow: hidden;
  z-index: 1000;
}

.register-container {
  max-width: 800px;
  width: 90vw;
  min-height: 520px;
  display: flex;
  background-color: rgba(255, 255, 255, 0.92);
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
  overflow: hidden;
  position: relative;
  z-index: 1;
  margin: 0 auto;
}

.register-info {
  width: 50%;
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

.register-info::before {
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
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
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
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.register-form-container {
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
  from { transform: translateY(80px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.register-form-header {
  margin-bottom: 32px;
  text-align: center;
}

.register-form-header h2 {
  font-size: 25px;
  color: #222;
  font-family: 'SimSun', '宋体', serif;
  font-weight: 600;
  letter-spacing: 2px;
  position: relative;
  display: inline-block;
}

.register-form-header h2::after {
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

.register-form {
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

.agreement {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  font-size: 14px;
  color: #888;
  font-family: 'SimSun', '宋体', serif;
  margin-bottom: 8px;
  gap: 2px;
  line-height: 1.6;
}

.agreement a, .agreement .agreement-link {
  display: inline;
  vertical-align: middle;
  white-space: nowrap;
  color: #222;
  text-decoration: underline;
  cursor: pointer;
  margin: 0 2px;
}

.register-button {
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

.register-button:hover {
  background: #444;
  color: #fff;
}

.form-footer {
  margin-top: 18px;
  text-align: center;
  font-size: 15px;
  font-family: 'SimSun', '宋体', serif;
  color: #888;
}

.register-link {
  color: #767676;
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
  .register-container {
    width: 98vw;
    min-width: 320px;
    flex-direction: column;
    height: auto;
  }
  .register-info, .register-form-container {
    width: 100%;
    min-width: 0;
    border-radius: 0;
    padding: 24px 10vw;
  }
  .register-form-container {
    border-left: none;
    border-top: 1.5px solid rgba(200,200,200,0.08);
  }
}
</style>
