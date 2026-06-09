<script setup lang="ts">
defineProps<{ value: string | number; label: string; trend?: 'up' | 'down' | 'neutral' }>()
</script>
<template>
  <div class="stat-card">
    <div class="value" :class="{ up: trend === 'up', down: trend === 'down' }">{{ value }}</div>
    <div class="label">{{ label }}</div>
  </div>
</template>
<style scoped>
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 12px; text-align: center; }
.value { font-size: 22px; font-weight: 700; color: var(--text); font-family: var(--font-mono); }
.value.up { color: var(--green); } .value.down { color: var(--red); }
.label { font-size: 11px; color: var(--muted); margin-top: 4px; }
</style>
