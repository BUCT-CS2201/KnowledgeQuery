<template>
  <div class="register-page">
    <div class="register-container">
      <!-- 左侧信息部分 -->
      <div class="register-info">
        <div class="register-info-content">
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
              <a href="javascript:void(0)">《用户协议》</a>和<a href="javascript:void(0)">《隐私政策》</a>
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
            <router-link to="/login">返回登录</router-link>
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
  min-height: 100vh;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  position: fixed;
  background-color: #f5f7fa;
}

.register-container {
  width: 800px;
  display: flex;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
  overflow: hidden;
}

/* 左侧信息样式 */
.register-info {
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
.register-form-container {
  width: 450px;
  padding: 30px;
}

.register-form-header {
  margin-bottom: 20px;
  text-align: center;
}

.register-form-header h2 {
  font-size: 20px;
  color: #333;
}

.register-form {
  width: 100%;
}

.agreement {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  font-size: 14px;
}

.agreement a {
  color: #1890ff;
  text-decoration: none;
}

.register-button {
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
  .register-container {
    width: 95%;
    flex-direction: column;
  }
  
  .register-form-container {
    width: 100%;
  }
}
</style>
