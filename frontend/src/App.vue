<script setup lang="ts">
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
auth.fetchUser()
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="view" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>
