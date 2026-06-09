<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ hint?: string }>()
const emit = defineEmits<{ search: [query: string] }>()

const query = ref('')
let timer: ReturnType<typeof setTimeout>

function onInput() {
  clearTimeout(timer)
  timer = setTimeout(() => emit('search', query.value), 300)
}
</script>

<template>
  <div class="search-bar">
    <input
      v-model="query"
      type="text"
      placeholder="搜索饰品名（如 AK-47 红线 久经）"
      @input="onInput"
    />
    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<style scoped>
.search-bar { padding: 0 0 12px; }
.search-bar input { width: 100%; padding: 14px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); color: var(--text); font-size: 15px; font-family: var(--font-sans); outline: none; }
.search-bar input::placeholder { color: var(--muted); }
.search-bar input:focus { border-color: var(--accent); }
.hint { font-size: 11px; color: var(--green); margin-top: 6px; padding-left: 4px; }
</style>
