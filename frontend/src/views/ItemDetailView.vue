<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api/client'
import AppLayout from '../components/AppLayout.vue'
import PlatformPrices from '../components/PlatformPrices.vue'

interface ItemDetail {
  id: number
  market_hash_name: string
  target_price: number | null
  mode: number
  enabled: boolean
  prices: { buff?: number; yyyp?: number; c5?: number; steam?: number }
  img_url: string | null
}

const route = useRoute()
const router = useRouter()
const item = ref<ItemDetail | null>(null)
const targetPrice = ref('')
const mode = ref(1)
const loading = ref(true)
const saving = ref(false)

async function load() {
  try {
    item.value = await api.get<ItemDetail>(`/watchlist/${route.params.id}`)
    if (item.value) {
      targetPrice.value = item.value.target_price?.toString() || ''
      mode.value = item.value.mode
    }
  } catch (e) {
    console.error(e)
    router.push('/')
  } finally {
    loading.value = false
  }
}

async function save() {
  if (!item.value) return
  saving.value = true
  try {
    await api.patch(`/watchlist/${item.value.id}`, {
      target_price: parseFloat(targetPrice.value) || null,
      mode: mode.value,
    })
    router.push('/')
  } catch (e) {
    console.error(e)
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!item.value || !confirm('确认删除此监控项？')) return
  try {
    await api.delete(`/watchlist/${item.value.id}`)
    router.push('/')
  } catch (e) {
    console.error(e)
  }
}

onMounted(load)
</script>

<template>
  <AppLayout>
    <div v-if="loading" class="empty">加载中...</div>
    <template v-else-if="item">
      <PlatformPrices :prices="item.prices" :img-url="item.img_url ?? undefined" :item-name="item.market_hash_name" />
      <div class="section">
        <div class="section-title">监控设置</div>
        <div class="setting-item">
          <span class="label">目标价</span>
          <input v-model="targetPrice" type="number" step="0.01" placeholder="¥ 目标价" />
        </div>
        <div class="setting-item">
          <span class="label">监控模式</span>
          <select v-model.number="mode">
            <option :value="1">盯价</option>
            <option :value="2">持仓</option>
          </select>
        </div>
        <div class="actions">
          <button class="btn-save" :disabled="saving" @click="save">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button class="btn-delete" @click="remove">删除</button>
        </div>
      </div>
    </template>
  </AppLayout>
</template>

<style scoped>
.section { padding: 0 20px; margin-top: 16px; }
.section-title { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; font-weight: 600; }
.setting-item { display: flex; align-items: center; justify-content: space-between; padding: 16px 0; border-bottom: 1px solid var(--border); }
.label { font-size: 14px; color: var(--text); }
.setting-item input { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 10px; border-radius: 8px; font-size: 13px; width: 60%; text-align: right; font-family: var(--font-mono); outline: none; }
.setting-item input:focus { border-color: var(--accent); }
.setting-item select { background: var(--bg); border: 1px solid var(--border); color: var(--text); padding: 10px; border-radius: 8px; font-size: 13px; outline: none; }
.actions { display: flex; gap: 8px; margin-top: 16px; }
.btn-save { flex: 1; padding: 14px; background: var(--green); color: #000; border: none; border-radius: var(--radius); font-size: 14px; font-weight: 700; cursor: pointer; font-family: var(--font-sans); }
.btn-save:disabled { opacity: 0.6; }
.btn-delete { padding: 14px 20px; background: transparent; color: var(--red); border: 1px solid var(--red); border-radius: var(--radius); font-size: 14px; cursor: pointer; font-family: var(--font-sans); }
.empty { text-align: center; padding: 40px 20px; color: var(--muted); }
</style>
