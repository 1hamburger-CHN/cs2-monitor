import anime from 'animejs'
import { onMounted, watch, type Ref } from 'vue'

/** Number counting from 0 to target (use with v-text or innerHTML binding) */
export function animateCount(el: HTMLElement, target: number, duration = 800) {
  anime({ targets: el, innerHTML: [0, target], round: 1, duration, easing: 'easeOutExpo' })
}

/** Staggered list entrance — call in onMounted */
export function animateListEntrance(selector: string) {
  anime({
    targets: selector,
    translateX: [-16, 0],
    opacity: [0, 1],
    delay: anime.stagger(40),
    duration: 280,
    easing: 'easeOutQuad',
  })
}

/** Price change flash background */
export function animatePriceFlash(el: HTMLElement, isUp: boolean) {
  const color = isUp ? '#22C55E44' : '#EF444444'
  anime({ targets: el, backgroundColor: [color, 'transparent'], duration: 600, easing: 'easeOutQuad' })
}

/** Pulse animation for alert indicators */
export function animatePulse(selector: string) {
  anime({
    targets: selector,
    scale: [1, 1.4],
    opacity: [1, 0],
    loop: false,
    duration: 800,
    easing: 'easeOutQuad',
  })
}

/** Page enter transition — call in onMounted of layout */
export function animatePageEnter(el: HTMLElement) {
  anime({ targets: el, opacity: [0, 1], translateY: [10, 0], duration: 220, easing: 'easeOutQuad' })
}

// ── Vue composables ──

/** Reactively animate a number displayed in a DOM element */
export function useCountAnimation(
  targetRef: Ref<HTMLElement | undefined>,
  value: Ref<number>,
) {
  onMounted(() => {
    watch(value, (v) => {
      if (targetRef.value && v > 0) animateCount(targetRef.value, v, 600)
    }, { immediate: true })
  })
}

/** Trigger list entrance animation after data loads */
export function useListEntrance(selector: string, trigger: Ref<boolean>) {
  watch(trigger, (loaded) => {
    if (loaded) {
      requestAnimationFrame(() => animateListEntrance(selector))
    }
  })
}
