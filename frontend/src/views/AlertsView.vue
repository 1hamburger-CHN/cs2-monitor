<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api/client'
import AppLayout from '../components/AppLayout.vue'
import AlertCard from '../components/AlertCard.vue'

interface AlertItem {
  id: number
  message: string
  sent_at: string
  rule_type: number
  market_hash_name: string
}

interface AlertsData { items: AlertItem[]; total: number }

const data = ref<AlertsData>({ items: [], total: 0 })
const loading = ref(true)

async function load() {
  try {
    data.value = await api.get<AlertsData>('/alerts?limit=50')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')} · ${d.getMonth() + 1}/${d.getDate()}`
}

function isTrigger(item: AlertItem): boolean {
  return item.rule_type !== 0 // 0 = daily report
}

onMounted(load)
</script>

<template>
  <AppLayout>
    <div class="header">
      <div class="title">告警中心</div>
      <div class="subtitle">
        今日 {{ data.total }} 条 · 历史 {{ data.total }} 条
      </div>
    </div>
    <div class="section">
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="!data.items.length" class="empty">暂无告警记录</div>
      <AlertCard
        v-for="item in data.items" :key="item.id"
        :time="formatTime(item.sent_at)"
        :message="item.message"
        :type="isTrigger(item) ? 'trigger' : 'daily'"
      />
    </div>
  </AppLayout>
</template>

<style scoped>
.header { padding: 24px 20px 16px; }
.title { font-size: 24px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.subtitle { font-size: 12px; color: var(--green); margin-top: 4px; font-family: var(--font-mono); }
.section { padding: 0 20px; }
.empty { text-align: center; padding: 40px 20px; color: var(--muted); font-size: 14px; }
</style>
