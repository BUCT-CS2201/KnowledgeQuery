<template>
  <div class="agreement-page">
    <h1>用户协议</h1>
    <p>你好啊，{{ userInfo }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const userInfo = ref('')
onMounted(() => {
  const user = localStorage.getItem('user')
  userInfo.value = user ? JSON.parse(user).name : '未登录用户'
})
</script>

<style scoped>
.agreement-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #222;
  background: #fff;
}
</style> 