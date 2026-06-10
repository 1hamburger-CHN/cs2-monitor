<script setup lang="ts">
import { onMounted } from 'vue'
import { animatePulse } from '../composables/useAnime'

const props = defineProps<{
  time: string
  message: string
  type: 'trigger' | 'daily'
}>()

onMounted(() => {
  if (props.type === 'trigger') {
    requestAnimationFrame(() => animatePulse('.alert-badge-pulse'))
  }
})
</script>

<template>
  <div class="alert alert-card" :class="{ trigger: type === 'trigger', daily: type === 'daily' }">
    <div class="time">{{ time }}</div>
    <div class="msg" v-html="message"></div>
    <span v-if="type === 'trigger'" class="badge badge-alert alert-badge-pulse">触发告警</span>
    <span v-else class="badge badge-info">日报</span>
  </div>
</template>

<style scoped>
.alert { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 10px; }
.alert.trigger { border-left: 3px solid var(--red); }
.alert.daily { border-left: 3px solid var(--accent); }
.time { font-size: 11px; color: var(--muted); margin-bottom: 8px; }
.msg { font-size: 14px; line-height: 1.6; color: var(--text); }
.badge { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 600; margin-top: 8px; }
.badge-alert { background: #EF444422; color: var(--red); }
.badge-info { background: #3B82F622; color: var(--accent); }
</style>
