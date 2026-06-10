<script setup lang="ts">
import PriceDisplay from './PriceDisplay.vue'

const props = defineProps<{
  id?: number
  name: string
  weapon?: string
  wearCn?: string
  imgUrl?: string
  price?: number
  targetPrice?: number
  platform?: string
  mode?: number
  clickable?: boolean
}>()

const emit = defineEmits<{ click: []; add: [] }>()
</script>

<template>
  <div class="item watchlist-item" :class="{ clickable }" @click="clickable && emit('click')">
    <img v-if="imgUrl" :src="imgUrl" width="48" height="48" alt="" class="item-img" loading="lazy"
      @error="(e: Event) => (e.target as HTMLImageElement).style.display = 'none'" />
    <div v-else class="item-img-placeholder"></div>
    <div class="item-info">
      <div class="item-name">{{ name }}</div>
      <div class="item-meta">
        <span v-if="weapon">{{ weapon }}</span>
        <span v-if="wearCn">{{ wearCn }}</span>
        <span v-if="platform">{{ platform }}</span>
      </div>
    </div>
    <div class="item-right">
      <div v-if="price !== undefined" class="price">
        <PriceDisplay :price="price" />
        <div v-if="targetPrice" class="target">目标 ¥{{ targetPrice.toFixed(2) }}</div>
      </div>
      <button v-else class="add-btn" @click.stop="emit('add')">添加</button>
    </div>
  </div>
</template>

<style scoped>
.item { display: flex; align-items: center; gap: 12px; padding: 14px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 8px; min-height: 66px; transition: background 0.15s; }
.item.clickable { cursor: pointer; }
.item.clickable:active { background: #1a2332; }
.item-img { width: 48px; height: 48px; border-radius: 6px; object-fit: cover; background: var(--border); flex-shrink: 0; }
.item-img-placeholder { width: 48px; height: 48px; border-radius: 6px; background: var(--border); flex-shrink: 0; }
.item-info { flex: 1; min-width: 0; }
.item-name { font-size: 14px; font-weight: 500; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.item-meta { font-size: 11px; color: var(--muted); margin-top: 3px; display: flex; gap: 8px; }
.item-right { text-align: right; flex-shrink: 0; }
.target { font-size: 11px; color: var(--muted); margin-top: 2px; }
.add-btn { background: var(--green); color: #000; border: none; padding: 8px 16px; border-radius: var(--radius); font-size: 13px; font-weight: 600; cursor: pointer; }
</style>
