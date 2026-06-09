<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import anime from 'animejs'

const props = defineProps<{
  price: number
  previousPrice?: number
}>()

const displayRef = ref<HTMLSpanElement>()

watch(() => props.price, (newVal, oldVal) => {
  if (displayRef.value && oldVal !== undefined && newVal !== oldVal) {
    const diff = newVal - oldVal
    const color = diff > 0 ? '#22C55E44' : diff < 0 ? '#EF444444' : 'transparent'
    anime({ targets: displayRef.value, backgroundColor: [color, 'transparent'], duration: 600, easing: 'easeOutQuad' })
  }
})

const direction = computed(() => {
  if (props.previousPrice === undefined) return ''
  if (props.price > props.previousPrice) return 'up'
  if (props.price < props.previousPrice) return 'down'
  return ''
})
</script>

<template>
  <span ref="displayRef" class="price-display" :class="direction">
    ¥{{ price.toFixed(2) }}
  </span>
</template>

<style scoped>
.price-display { font-size: 18px; font-weight: 700; font-family: var(--font-mono); padding: 2px 6px; border-radius: 4px; }
.price-display.up { color: var(--green); }
.price-display.down { color: var(--red); }
</style>
