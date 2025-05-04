<template>
  <div class="auth-container">
    <h2 class="auth-title">登录</h2>
    
    <el-form 
      :model="form" 
      :rules="rules" 
      ref="formRef" 
      label-width="80px" 
      @submit.prevent="handleLogin"
    >
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名"></el-input>
      </el-form-item>
      
      <el-form-item label="密码" prop="password">
        <el-input 
          v-model="form.password" 
          type="password" 
          placeholder="请输入密码"
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
          登录
        </el-button>
      </el-form-item>
    </el-form>
    
    <div v-if="error" class="error-message">
      <el-alert :title="error" type="error" show-icon />
    </div>
    
    <div class="auth-footer">
      还没有账号？ <router-link to="/register">立即注册</router-link>
    </div>
  </div>
</template>

<script>
import { ref, computed, reactive } from 'vue'
import { useAuthStore } from '../store/auth'

export default {
  name: 'LoginView',
  setup() {
    const authStore = useAuthStore()
    const formRef = ref(null)
    
    const form = reactive({
      username: '',
      password: ''
    })
    
    const rules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度至少6个字符', trigger: 'blur' }
      ]
    }
    
    const loading = computed(() => authStore.getLoading)
    const error = computed(() => authStore.getError)
    
    const handleLogin = async () => {
      if (!formRef.value) return
      
      await formRef.value.validate(async (valid) => {
        if (valid) {
          await authStore.login(form.username, form.password)
        }
      })
    }
    
    return {
      form,
      rules,
      formRef,
      handleLogin,
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