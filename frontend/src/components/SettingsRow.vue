<script setup lang="ts">
defineProps<{ label: string; value?: string }>()
</script>

<template>
  <div class="setting-item">
    <span class="label">{{ label }}</span>
    <span class="value" v-if="value">{{ value }}</span>
    <slot v-else></slot>
  </div>
</template>

<style scoped>
.setting-item { display: flex; align-items: center; justify-content: space-between; padding: 16px 0; border-bottom: 1px solid var(--border); }
.label { font-size: 14px; color: var(--text); }
.value { font-size: 13px; color: var(--muted); }
</style>
