<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'
import AppLayout from '../components/AppLayout.vue'
import SettingsRow from '../components/SettingsRow.vue'

interface UserSettings {
  server_chan_key_masked: string
  steam_id: string
  preferred_source: string
}

const router = useRouter()
const auth = useAuthStore()
const settings = ref<UserSettings>({ server_chan_key_masked: '', steam_id: '', preferred_source: 'csqaq' })
const serverChanKey = ref('')
const steamId = ref('')
const steamApiKey = ref('')
const preferredSource = ref('csqaq')
const saving = ref(false)
const message = ref('')

async function load() {
  try {
    settings.value = await api.get<UserSettings>('/settings')
    steamId.value = settings.value.steam_id
    preferredSource.value = settings.value.preferred_source
  } catch (e) {
    console.error(e)
  }
}

async function save() {
  saving.value = true
  message.value = ''
  try {
    await api.put('/settings', {
      server_chan_key: serverChanKey.value || undefined,
      steam_id: steamId.value,
      steam_api_key: steamApiKey.value || undefined,
      preferred_source: preferredSource.value,
    })
    message.value = '设置已保存'
    serverChanKey.value = ''
    steamApiKey.value = ''
  } catch (e: any) {
    message.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function doLogout() {
  await auth.logout()
  router.push('/login')
}

onMounted(load)
</script>

<template>
  <AppLayout>
    <div class="header"><div class="title">设置</div></div>
    <div class="section">
      <div class="section-title">通知</div>
      <SettingsRow label="Server酱 SendKey" :value="settings.server_chan_key_masked || '未设置'" />
      <input v-model="serverChanKey" type="text" placeholder="新 SendKey（留空不修改）" />
    </div>
    <div class="section">
      <div class="section-title">Steam 配置</div>
      <SettingsRow label="Steam ID">
        <input v-model="steamId" type="text" placeholder="7656119xxxxxxxx" />
      </SettingsRow>
      <input v-model="steamApiKey" type="text" placeholder="Steam Web API Key（留空不修改）" style="margin-top:8px" />
    </div>
    <div class="section">
      <div class="section-title">价格数据源</div>
      <SettingsRow label="首选数据源">
        <select v-model="preferredSource">
          <option value="csqaq">CSQAQ</option>
          <option value="steamdt">SteamDT</option>
        </select>
      </SettingsRow>
      <div class="status">
        <span class="dot"></span> {{ preferredSource === 'csqaq' ? 'CSQAQ' : 'SteamDT' }} · 已连接
      </div>
    </div>
    <div v-if="message" class="message" :class="{ success: message.includes('已保存') }">{{ message }}</div>
    <div class="section">
      <button class="btn-save" :disabled="saving" @click="save">
        {{ saving ? '保存中...' : '保存设置' }}
      </button>
    </div>
    <div class="section">
      <button class="btn-logout" @click="doLogout">退出登录</button>
    </div>
  </AppLayout>
</template>

<style scoped>
.header { padding: 24px 20px 16px; }
.title { font-size: 24px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.section { padding: 0 20px; margin-bottom: 16px; }
.section-title { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: 600; }
.section input { width: 100%; padding: 10px; background: var(--bg); border: 1px solid var(--border); color: var(--text); border-radius: 8px; font-size: 13px; font-family: var(--font-mono); outline: none; }
.section input:focus { border-color: var(--accent); }
.section select { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 10px; border-radius: 8px; font-size: 13px; outline: none; }
.status { font-size: 13px; color: var(--green); margin-top: 8px; display: flex; align-items: center; gap: 6px; }
.dot { width: 8px; height: 8px; background: var(--green); border-radius: 50%; }
.message { padding: 12px; border-radius: var(--radius); margin: 0 20px 12px; font-size: 14px; background: #3B82F622; color: var(--accent); }
.message.success { background: #22C55E22; color: var(--green); }
.btn-save { width: 100%; padding: 14px; background: var(--green); color: #000; border: none; border-radius: var(--radius); font-size: 14px; font-weight: 700; cursor: pointer; font-family: var(--font-sans); }
.btn-save:disabled { opacity: 0.6; }
.btn-logout { width: 100%; padding: 14px; background: transparent; color: var(--red); border: 1px solid var(--red); border-radius: var(--radius); font-size: 14px; cursor: pointer; font-family: var(--font-sans); }
</style>
