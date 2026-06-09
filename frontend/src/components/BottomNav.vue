<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
function isActive(tab: string) {
  const map: Record<string, string> = { dashboard: '/', alerts: '/alerts', add: '/add', settings: '/settings' }
  return route.path === map[tab]
}
</script>

<template>
  <nav class="bottom-nav">
    <router-link to="/" class="nav-item" :class="{ active: isActive('dashboard') }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon">
        <rect x="3" y="3" width="18" height="18" rx="3"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
      </svg><span>首页</span>
    </router-link>
    <router-link to="/alerts" class="nav-item" :class="{ active: isActive('alerts') }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg><span>告警</span>
    </router-link>
    <router-link to="/add" class="nav-item" :class="{ active: isActive('add') }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
      </svg><span>添加</span>
    </router-link>
    <router-link to="/settings" class="nav-item" :class="{ active: isActive('settings') }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="nav-icon">
        <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg><span>设置</span>
    </router-link>
  </nav>
</template>

<style scoped>
.bottom-nav { display: flex; justify-content: space-around; align-items: center; height: 70px; background: var(--surface); border-top: 1px solid var(--border); position: fixed; bottom: 0; left: 50%; transform: translateX(-50%); width: 100%; max-width: 480px; padding-bottom: env(safe-area-inset-bottom, 0); z-index: 100; }
@media (min-width: 768px) { .bottom-nav { max-width: 720px; } }
.nav-item { display: flex; flex-direction: column; align-items: center; gap: 4px; color: var(--muted); font-size: 11px; cursor: pointer; padding: 8px 16px; border-radius: var(--radius); transition: color 0.2s; min-width: 64px; min-height: 44px; justify-content: center; text-decoration: none; }
.nav-item.active { color: var(--green); }
.nav-icon { width: 22px; height: 22px; }
</style>
