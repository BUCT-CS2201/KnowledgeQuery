<template>
  <div class="container">
    <el-card class="welcome-card">
      <template #header>
        <div class="card-header">
          <h3>欢迎使用认证系统，{{ user ? user.username : '用户' }}</h3>
        </div>
      </template>
      <div class="card-content">
        <p>这是一个简单的认证系统示例，包含登录和注册功能。</p>
        <p>您已成功登录系统，可以查看个人资料或者管理其他功能。</p>
        
        <div class="action-buttons">
          <el-button type="primary" @click="$router.push('/profile')">
            查看个人资料
          </el-button>
          <el-button @click="logout">退出登录</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { useAuthStore } from '../store/auth'
import { computed } from 'vue'

export default {
  name: 'HomeView',
  setup() {
    const authStore = useAuthStore()
    
    const user = computed(() => authStore.getUser)
    
    const logout = () => {
      authStore.logout()
    }
    
    return {
      user,
      logout
    }
  }
}
</script>

<style scoped>
.welcome-card {
  margin-top: 40px;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-content {
  padding: 20px 0;
  line-height: 1.8;
}

.action-buttons {
  margin-top: 30px;
  display: flex;
  gap: 15px;
}
</style> 