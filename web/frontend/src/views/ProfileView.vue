<template>
  <div class="container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <h3>个人资料</h3>
        </div>
      </template>
      
      <div class="card-content" v-if="user">
        <el-descriptions title="用户信息" :column="1" border>
          <el-descriptions-item label="用户名">{{ user.username }}</el-descriptions-item>
          <el-descriptions-item label="邮箱">{{ user.email }}</el-descriptions-item>
          <el-descriptions-item label="账号状态">
            <el-tag type="success" v-if="user.is_active">正常</el-tag>
            <el-tag type="danger" v-else>禁用</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="注册时间">
            {{ formatDate(user.created_at) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="action-buttons">
          <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
        </div>
      </div>
      
      <div v-else class="loading-container">
        <el-skeleton :rows="4" animated />
      </div>
    </el-card>
  </div>
</template>

<script>
import { useAuthStore } from '../store/auth'
import { computed, onMounted } from 'vue'

export default {
  name: 'ProfileView',
  setup() {
    const authStore = useAuthStore()
    
    const user = computed(() => authStore.getUser)
    
    onMounted(() => {
      // 刷新用户数据
      authStore.fetchUserProfile()
    })
    
    const formatDate = (dateString) => {
      if (!dateString) return '未知'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    return {
      user,
      formatDate
    }
  }
}
</script>

<style scoped>
.profile-card {
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
}

.action-buttons {
  margin-top: 30px;
  display: flex;
  justify-content: center;
}

.loading-container {
  padding: 20px;
}
</style> 