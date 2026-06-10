<script setup lang="ts">
import { ref, watch } from 'vue'
import { animateCount } from '../composables/useAnime'

const props = defineProps<{ value: string | number; label: string; trend?: 'up' | 'down' | 'neutral' }>()

const valueRef = ref<HTMLDivElement>()

let animated = false
watch(() => props.value, (val) => {
  const num = typeof val === 'number' ? val : parseFloat(String(val))
  if (!valueRef.value || isNaN(num) || num <= 0) return
  if (!animated && num > 0) {
    animated = true
    valueRef.value.textContent = '0'
    animateCount(valueRef.value, num, 1000)
  }
})
</script>
<template>
  <div class="stat-card">
    <div ref="valueRef" class="value" :class="{ up: trend === 'up', down: trend === 'down' }">{{ value }}</div>
    <div class="label">{{ label }}</div>
  </div>
</template>
<style scoped>
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 12px; text-align: center; }
.value { font-size: 22px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.value.up { color: var(--green); } .value.down { color: var(--red); }
.label { font-size: 11px; color: var(--muted); margin-top: 4px; }
</style>
