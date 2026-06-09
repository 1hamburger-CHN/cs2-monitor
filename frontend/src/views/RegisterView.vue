<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const inviteCode = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  if (password.value.length < 6) { error.value = '密码至少6位'; return }
  loading.value = true
  try {
    await auth.register(username.value, password.value, inviteCode.value)
    router.push('/')
  } catch (e: any) {
    error.value = e.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="header">
      <div class="title">创建账号</div>
      <div class="subtitle">需要邀请码才能注册</div>
    </div>
    <form class="form" @submit.prevent="onSubmit">
      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <input v-model="username" type="text" placeholder="用户名" required autocomplete="username" />
      <input v-model="password" type="password" placeholder="密码（至少6位）" required autocomplete="new-password" />
      <input v-model="inviteCode" type="text" placeholder="邀请码" required />
      <button type="submit" :disabled="loading">
        {{ loading ? '注册中...' : '注册' }}
      </button>
    </form>
    <p class="footer">
      已有账号？<router-link to="/login">登录</router-link>
    </p>
  </div>
</template>

<style scoped>
.auth-page { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; padding: 32px 20px; }
.header { text-align: center; margin-bottom: 40px; }
.title { font-size: 28px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.subtitle { font-size: 13px; color: var(--muted); margin-top: 8px; }
.form { width: 100%; max-width: 320px; }
.form input { width: 100%; padding: 14px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); font-size: 15px; margin-bottom: 12px; outline: none; font-family: var(--font-sans); }
.form input:focus { border-color: var(--accent); }
.form button { width: 100%; padding: 14px; background: var(--green); color: #000; border: none; border-radius: var(--radius); font-size: 15px; font-weight: 700; cursor: pointer; font-family: var(--font-sans); }
.form button:disabled { opacity: 0.6; }
.alert-error { padding: 12px; background: #EF444422; border: 1px solid var(--red); border-radius: var(--radius); color: var(--red); margin-bottom: 16px; font-size: 14px; }
.footer { margin-top: 24px; font-size: 14px; color: var(--muted); }
.footer a { color: var(--accent); }
</style>
