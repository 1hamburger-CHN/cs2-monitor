<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import AppLayout from '../components/AppLayout.vue'
import SearchBar from '../components/SearchBar.vue'
import WatchlistItem from '../components/WatchlistItem.vue'

interface SearchResult {
  market_hash_name: string
  weapon: string
  wear_cn: string
  img_url: string | null
}

const router = useRouter()
const results = ref<SearchResult[]>([])
const hint = ref('')
const adding = ref<string | null>(null)
const error = ref('')

async function search(query: string) {
  if (!query.trim()) { results.value = []; hint.value = ''; return }
  try {
    const data = await api.get<SearchResult[]>(`/items/search?q=${encodeURIComponent(query)}&limit=20`)
    results.value = data
    hint.value = `匹配 ${data.length} 件饰品`
  } catch (e) {
    console.error(e)
  }
}

async function addItem(itemName: string) {
  error.value = ''
  adding.value = itemName
  try {
    await api.post('/watchlist', { item_name: itemName, target_price: 0, mode: 1 })
    router.push('/')
  } catch (e: any) {
    error.value = e.message || '添加失败'
  } finally {
    adding.value = null
  }
}
</script>

<template>
  <AppLayout>
    <div class="header">
      <div class="title">添加监控</div>
      <div class="subtitle">搜索饰品名加入监控列表</div>
    </div>
    <div class="section">
      <SearchBar :hint="hint" @search="search" />
      <div v-if="error" class="alert-error">{{ error }}</div>
      <WatchlistItem
        v-for="item in results" :key="item.market_hash_name"
        :name="item.market_hash_name"
        :weapon="item.weapon"
        :wear-cn="item.wear_cn"
        :img-url="item.img_url ?? undefined"
        @add="addItem(item.market_hash_name)"
      />
      <div v-if="results.length === 0 && hint" class="empty">未找到匹配饰品</div>
    </div>
  </AppLayout>
</template>

<style scoped>
.header { padding: 24px 20px 16px; }
.title { font-size: 24px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.subtitle { font-size: 12px; color: var(--green); margin-top: 4px; font-family: var(--font-mono); }
.section { padding: 0 20px; }
.empty { text-align: center; padding: 40px 20px; color: var(--muted); font-size: 14px; }
.alert-error { padding: 12px; background: #EF444422; border: 1px solid var(--red); border-radius: var(--radius); color: var(--red); margin-bottom: 12px; font-size: 14px; }
</style>
