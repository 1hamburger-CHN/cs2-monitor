import anime from 'animejs'

/** Slot-machine scroll: numbers tumble down from 0 to target */
export function animateCount(el: HTMLElement, target: number, duration = 1800) {
  if (target <= 0) return

  const cs = getComputedStyle(el)
  const rowH = parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.4 || 28

  const spin = Array.from({ length: 12 }, () => Math.floor(Math.random() * 9) + 1)
  // For large targets, sample ~15 numbers to keep DOM light
  const showAll = target <= 50
  const real = showAll
    ? Array.from({ length: target + 1 }, (_, i) => i)
    : (() => {
        const tail: number[] = [0]
        const step = Math.max(1, Math.floor(target / 15))
        for (let v = step; v < target; v += step) tail.push(v)
        tail.push(target)
        return tail
      })()
  const strip = [...spin, ...real]

  // Use bounding rect for accurate width (works on inline elements too)
  const rect = el.getBoundingClientRect()
  const elWidth = rect.width

  const box = document.createElement('span')
  box.style.cssText = `display:inline-block;overflow:hidden;vertical-align:baseline;height:${rowH}px;width:${elWidth}px`

  const reel = document.createElement('span')
  reel.style.cssText = 'display:inline-block'

  strip.forEach((n) => {
    const cell = document.createElement('div')
    cell.style.cssText = `height:${rowH}px;line-height:${rowH}px;text-align:center;font:${cs.font};color:${cs.color}`
    cell.textContent = String(n)
    reel.appendChild(cell)
  })

  box.appendChild(reel)
  el.replaceWith(box)

  const startIdx = spin.length
  const endIdx = strip.length - 1
  const totalRows = endIdx - startIdx

  anime({
    targets: reel,
    translateY: [-(startIdx * rowH), -(endIdx * rowH)],
    duration: duration + totalRows * 80,
    easing: 'easeOutQuad',
    complete: () => {
      box.replaceWith(el)
      el.textContent = String(target)
    },
  })
}

/** Staggered list entrance */
export function animateListEntrance(selector: string) {
  anime({
    targets: selector,
    translateX: [-20, 0],
    opacity: [0, 1],
    delay: anime.stagger(60),
    duration: 400,
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

/** Page enter transition */
export function animatePageEnter(el: HTMLElement) {
  anime({ targets: el, opacity: [0, 1], translateY: [10, 0], duration: 220, easing: 'easeOutQuad' })
}
