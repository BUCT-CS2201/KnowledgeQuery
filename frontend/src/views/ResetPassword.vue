<template>
  <div class="reset-password-page">
    <div class="reset-password-container">
      <div class="reset-password-header">
        <h2>重置密码</h2>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" class="reset-form">
        <el-form-item prop="new_password">
          <el-input v-model="form.new_password" type="password" placeholder="请输入新密码" maxlength="20" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item prop="confirm_password">
          <el-input v-model="form.confirm_password" type="password" placeholder="请确认新密码" maxlength="20" prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading" class="reset-button">提交</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { accountApi } from '../services/api'

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({
  new_password: '',
  confirm_password: ''
})
const rules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: (rule, value, callback) => {
      if (value !== form.new_password) {
        callback(new Error('两次输入的密码不一致'))
      } else {
        callback()
      }
    }, trigger: 'blur' }
  ]
}

const handleSubmit = () => {
  if (!formRef.value) return
  formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await accountApi.resetPassword({
          phone_number: route.query.phone,
          new_password: form.new_password
        })
        if (res.data.code === 200) {
          ElMessage.success('密码重置成功')
          router.push('/login')
        } else {
          ElMessage.error(res.data.message || '密码重置失败')
        }
      } catch (e) {
        ElMessage.error(e.response?.data?.message || '请求失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.reset-password-page {
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
.reset-password-container {
  max-width: 400px;
  width: 90vw;
  padding: 32px 28px;
  background-color: rgba(255, 255, 255, 0.92);
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.10);
  overflow: hidden;
  position: relative;
  z-index: 1;
  margin: 0 auto;
}
.reset-password-header {
  margin-bottom: 32px;
  text-align: center;
}
.reset-password-header h2 {
  font-size: 25px;
  color: #222;
  font-family: 'SimSun', '宋体', serif;
  font-weight: 600;
  letter-spacing: 2px;
  position: relative;
  display: inline-block;
}
.reset-password-header h2::after {
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
.reset-form {
  margin-top: 18px;
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
.reset-button {
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
.reset-button:hover {
  background: #444;
  color: #fff;
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
</style> 