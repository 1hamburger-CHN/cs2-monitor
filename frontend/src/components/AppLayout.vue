<script setup lang="ts">
import BottomNav from './BottomNav.vue'
</script>

<template>
  <div class="app-shell">
    <main class="content">
      <router-view v-slot="{ Component }">
        <transition name="view" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <BottomNav />
  </div>
</template>

<style scoped>
.app-shell { display: flex; flex-direction: column; min-height: 100vh; }
.content { flex: 1; overflow-y: auto; padding-bottom: 80px; }
</style>
