<template>
  <div id="app">
    <nav v-if="isAuthenticated" class="navbar">
      <div class="container">
        <h1 class="navbar-title">知识问答子系统</h1>
        <div class="navbar-links">
          <router-link to="/">问答对话</router-link>
          <router-link to="/profile">个人资料</router-link>
          <a href="#" @click.prevent="logout">退出登录</a>
        </div>
      </div>
    </nav>
    
    <router-view />
  </div>
</template>

<script>
import { useAuthStore } from './store/auth'
import { computed, onMounted } from 'vue'

export default {
  name: 'App',
  setup() {
    const authStore = useAuthStore()
    
    const isAuthenticated = computed(() => authStore.isAuthenticated)
    
    const logout = () => {
      authStore.logout()
    }
    
    onMounted(() => {
      // 如果有token，获取用户信息
      if (authStore.token) {
        authStore.fetchUserProfile()
      }
    })
    
    return {
      isAuthenticated,
      logout
    }
  }
}
</script>

<style>
.navbar {
  background-color: #0a84ff;
  color: white;
  padding: 15px 0;
  margin-bottom: 0;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
}

.navbar-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.navbar .container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-links {
  display: flex;
  gap: 20px;
}

.navbar-links a {
  color: white;
  text-decoration: none;
  font-weight: 500;
  padding: 5px 10px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.navbar-links a:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #f4f6f8;
  color: #333;
  height: 100vh;
}

* {
  box-sizing: border-box;
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style> 