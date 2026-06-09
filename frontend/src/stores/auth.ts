import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '../api/client'

export interface User {
  id: number
  username: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(true)

  async function fetchUser() {
    try {
      user.value = await api.get<User>('/me')
    } catch {
      user.value = null
    } finally {
      loading.value = false
    }
  }

  async function login(username: string, password: string) {
    const u = await api.post<User>('/auth/login', { username, password })
    user.value = u
  }

  async function register(username: string, password: string, inviteCode: string) {
    const u = await api.post<User>('/auth/register', { username, password, invite_code: inviteCode })
    user.value = u
  }

  async function logout() {
    await api.post('/auth/logout')
    user.value = null
  }

  return { user, loading, fetchUser, login, register, logout }
})
