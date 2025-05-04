<template>
  <div class="auth-container">
    <h2 class="auth-title">注册</h2>
    
    <el-form 
      :model="form" 
      :rules="rules" 
      ref="formRef" 
      label-width="80px" 
      @submit.prevent="handleRegister"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名"></el-input>
      </el-form-item>
      
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" placeholder="请输入邮箱"></el-input>
      </el-form-item>
      
      <el-form-item label="密码" prop="password">
        <el-input 
          v-model="form.password" 
          type="password" 
          placeholder="请输入密码"
          show-password
        ></el-input>
      </el-form-item>
      
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input 
          v-model="form.confirmPassword" 
          type="password" 
          placeholder="请再次输入密码"
          show-password
        ></el-input>
      </el-form-item>
      
      <el-form-item>
        <el-button 
          type="primary" 
          native-type="submit" 
          class="btn-block" 
          :loading="loading"
        >
          注册
        </el-button>
      </el-form-item>
    </el-form>
    
    <div v-if="error" class="error-message">
      <el-alert :title="error" type="error" show-icon />
    </div>
    
    <div class="auth-footer">
      已有账号？ <router-link to="/login">去登录</router-link>
    </div>
  </div>
</template>

<script>
import { ref, computed, reactive } from 'vue'
import { useAuthStore } from '../store/auth'

export default {
  name: 'RegisterView',
  setup() {
    const authStore = useAuthStore()
    const formRef = ref(null)
    
    const form = reactive({
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
    const validatePass = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请再次输入密码'))
      } else if (value !== form.password) {
        callback(new Error('两次输入密码不一致!'))
      } else {
        callback()
      }
    }
    
    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 50, message: '用户名长度在3到50个字符之间', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, validator: validatePass, trigger: 'blur' }
      ]
    }
    
    const loading = computed(() => authStore.getLoading)
    const error = computed(() => authStore.getError)
    
    const handleRegister = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (valid) {
          await authStore.register(form.username, form.email, form.password)
        }
      })
    }
    
    return {
      form,
      rules,
      formRef,
      handleRegister,
      loading,
      error
    }
  }
}
</script>

<style scoped>
.error-message {
  margin-top: 20px;
}
</style> 