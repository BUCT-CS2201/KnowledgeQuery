<template>
  <div class="forgot-password-page">
    <div class="forgot-password-container">
      <div class="forgot-password-header">
        <h2>找回密码</h2>
      </div>
      <el-form :model="form" :rules="rules" ref="formRef" class="forgot-form">
        <el-form-item prop="phone_number">
          <el-input v-model="form.phone_number" placeholder="请输入手机号" maxlength="11" prefix-icon="Phone" />
        </el-form-item>
        <el-form-item prop="id_number">
          <el-input v-model="form.id_number" placeholder="请输入身份证号" maxlength="18" prefix-icon="Document" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleNext" :loading="loading" class="forgot-button">下一步</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { accountApi } from '../services/api'

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const form = reactive({
  phone_number: '',
  id_number: ''
})
const rules = {
  phone_number: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的11位手机号码', trigger: 'blur' }
  ],
  id_number: [
    { required: true, message: '请输入身份证号', trigger: 'blur' },
    { min: 15, max: 18, message: '身份证号格式不正确', trigger: 'blur' }
  ]
}

const handleNext = () => {
  if (!formRef.value) return
  formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await accountApi.checkUserExist({
          phone_number: form.phone_number,
          id_number: form.id_number
        })
        if (res.data.code === 200 && res.data.data.exist) {
          ElMessage.success('验证成功')
          router.push({ path: '/reset-password', query: { phone: form.phone_number } })
        } else {
          ElMessage.error('您的账号或身份证填写错误')
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
.forgot-password-page {
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
.forgot-password-container {
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
.forgot-password-header {
  margin-bottom: 32px;
  text-align: center;
}
.forgot-password-header h2 {
  font-size: 25px;
  color: #222;
  font-family: 'SimSun', '宋体', serif;
  font-weight: 600;
  letter-spacing: 2px;
  position: relative;
  display: inline-block;
}
.forgot-password-header h2::after {
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
.forgot-form {
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
.forgot-button {
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
.forgot-button:hover {
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