import anime from 'animejs'

/** Animate number counting from 0 to target */
export function animateCount(el: HTMLElement, target: number, duration = 800) {
  anime({
    targets: el,
    innerHTML: [0, target],
    round: 1,
    duration,
    easing: 'easeOutExpo',
  })
}

/** Staggered list entrance */
export function animateListEntrance(selector: string) {
  anime({
    targets: selector,
    translateX: [-20, 0],
    opacity: [0, 1],
    delay: anime.stagger(50),
    duration: 300,
    easing: 'easeOutQuad',
  })
}

/** Price change flash */
export function animatePriceFlash(el: HTMLElement, isUp: boolean) {
  const color = isUp ? '#22C55E44' : '#EF444444'
  anime({
    targets: el,
    backgroundColor: [color, 'transparent'],
    duration: 600,
    easing: 'easeOutQuad',
  })
}

/** Pulse animation for alert indicators */
export function animatePulse(selector: string) {
  anime({
    targets: selector,
    scale: [1, 1.5],
    opacity: [1, 0],
    loop: true,
    duration: 1000,
    easing: 'easeInOutQuad',
  })
}

/** Page enter transition */
export function animatePageEnter(el: HTMLElement) {
  anime({
    targets: el,
    opacity: [0, 1],
    translateY: [8, 0],
    duration: 200,
    easing: 'easeOutQuad',
  })
}
