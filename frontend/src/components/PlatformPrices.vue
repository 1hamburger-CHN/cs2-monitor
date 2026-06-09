<script setup lang="ts">
defineProps<{
  prices: { buff?: number; yyyp?: number; c5?: number; steam?: number }
  imgUrl?: string
  itemName?: string
}>()
</script>

<template>
  <div class="detail-header">
    <img v-if="imgUrl" :src="imgUrl" width="140" height="105" alt="" class="detail-img"
      @error="(e: Event) => (e.target as HTMLImageElement).style.display = 'none'" />
    <div v-if="itemName" class="name">{{ itemName }}</div>
  </div>
  <div class="platforms">
    <div class="platform" v-if="prices.buff">
      <div class="p">¥{{ prices.buff?.toFixed(2) }}</div><div class="src">BUFF</div>
    </div>
    <div class="platform" v-if="prices.yyyp">
      <div class="p">¥{{ prices.yyyp?.toFixed(2) }}</div><div class="src">悠悠有品</div>
    </div>
    <div class="platform" v-if="prices.c5">
      <div class="p">¥{{ prices.c5?.toFixed(2) }}</div><div class="src">C5</div>
    </div>
    <div class="platform" v-if="prices.steam">
      <div class="p">${{ prices.steam?.toFixed(2) }}</div><div class="src">Steam</div>
    </div>
  </div>
</template>

<style scoped>
.detail-header { text-align: center; padding: 20px; }
.detail-img { width: 140px; height: 105px; border-radius: 8px; object-fit: cover; margin-bottom: 12px; background: var(--surface); }
.name { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.platforms { display: flex; gap: 8px; padding: 0 20px; overflow-x: auto; }
.platform { flex-shrink: 0; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 16px; text-align: center; min-width: 76px; }
.p { font-size: 18px; font-weight: 700; font-family: var(--font-mono); color: var(--text); }
.src { font-size: 10px; color: var(--muted); margin-top: 4px; }
</style>
