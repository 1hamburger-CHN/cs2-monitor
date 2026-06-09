<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import AppLayout from '../components/AppLayout.vue'
import StatCard from '../components/StatCard.vue'
import WatchlistItem from '../components/WatchlistItem.vue'

interface DashboardData {
  watchlist_count: number
  alert_count: number
  portfolio_value: number | null
  items: Array<{
    id: number
    market_hash_name: string
    target_price: number | null
    mode: number
    enabled: boolean
    latest_price: number | null
    img_url: string | null
    platform: string | null
  }>
}

const router = useRouter()
const data = ref<DashboardData>({ watchlist_count: 0, alert_count: 0, portfolio_value: null, items: [] })
const loading = ref(true)
const now = new Date()

const greeting = computed(() => {
  const h = now.getHours()
  if (h < 6) return '夜深了 🌙'
  if (h < 12) return '早上好 👋'
  if (h < 18) return '下午好 ☀️'
  return '晚上好 🌆'
})

async function load() {
  try {
    data.value = await api.get<DashboardData>('/dashboard')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)

function goToItem(id: number) {
  router.push(`/item/${id}`)
}

import { computed } from 'vue'
</script>

<template>
  <AppLayout>
    <div class="header">
      <div class="greeting">{{ greeting }}</div>
      <div class="title">CS2 Monitor</div>
      <div class="subtitle">● 实时监控中 · 5分钟刷新</div>
    </div>
    <div class="stats">
      <StatCard :value="data.watchlist_count" label="监控中" />
      <StatCard :value="data.portfolio_value ? '¥' + (data.portfolio_value / 1000).toFixed(1) + 'k' : '--'" label="持仓总值" trend="up" />
      <StatCard :value="data.alert_count" label="今日告警" :trend="data.alert_count > 0 ? 'down' : 'neutral'" />
    </div>
    <div class="section">
      <div class="section-title">监控列表</div>
      <div v-if="loading" class="empty">加载中...</div>
      <div v-else-if="!data.items.length" class="empty">
        暂无监控饰品<br />
        <router-link to="/add" class="link">去添加 →</router-link>
      </div>
      <WatchlistItem
        v-for="item in data.items" :key="item.id"
        :id="item.id"
        :name="item.market_hash_name"
        :price="item.latest_price ?? undefined"
        :target-price="item.target_price ?? undefined"
        :img-url="item.img_url ?? undefined"
        :platform="item.platform ?? undefined"
        :mode="item.mode"
        :clickable="true"
        @click="goToItem(item.id)"
      />
    </div>
  </AppLayout>
</template>

<style scoped>
.header { padding: 24px 20px 16px; }
.greeting { font-size: 13px; color: var(--muted); margin-bottom: 4px; }
.title { font-size: 24px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.subtitle { font-size: 12px; color: var(--green); margin-top: 4px; font-family: var(--font-mono); }
.stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; padding: 0 20px; margin-bottom: 20px; }
.section { padding: 0 20px; margin-bottom: 12px; }
.section-title { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: 600; }
.empty { text-align: center; padding: 40px 20px; color: var(--muted); font-size: 14px; }
.link { color: var(--accent); text-decoration: none; }
</style>
