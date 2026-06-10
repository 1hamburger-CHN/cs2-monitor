const CACHE_NAME = 'cs2-monitor-v2'
const SHELL = ['/']
const API_CACHE = 'cs2-api-v1'

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL))
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME && k !== API_CACHE).map((k) => caches.delete(k)))
    )
  )
  self.clients.claim()
})

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url)
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(event.request))
  } else {
    event.respondWith(cacheFirst(event.request))
  }
})

async function networkFirst(request) {
  try {
    const response = await fetch(request)
    const cache = await caches.open(API_CACHE)
    cache.put(request, response.clone())
    return response
  } catch {
    const cached = await caches.match(request)
    return cached || new Response('{}', { headers: { 'Content-Type': 'application/json' } })
  }
}

async function cacheFirst(request) {
  const cached = await caches.match(request)
  if (cached) return cached
  try {
    const response = await fetch(request)
    const cache = await caches.open(CACHE_NAME)
    cache.put(request, response.clone())
    return response
  } catch {
    return new Response('Offline', { status: 503 })
  }
}

self.addEventListener('push', (event) => {
  const data = event.data?.json() || { title: 'CS2 Monitor', body: '价格更新' }
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/icon-192.png',
      vibrate: [200, 100, 200],
      tag: data.tag || 'cs2-alert',
    })
  )
})

self.addEventListener('notificationclick', (event) => {
  event.notification.close()
  event.waitUntil(
    clients.openWindow('/alerts')
  )
})
