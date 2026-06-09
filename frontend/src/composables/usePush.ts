import { ref } from 'vue'
import { api } from '../api/client'

const supported = ref('serviceWorker' in navigator && 'PushManager' in window)
const permission = ref(Notification.permission)
const subscribed = ref(false)

async function subscribe() {
  if (!supported.value) return false
  const perm = await Notification.requestPermission()
  permission.value = perm
  if (perm !== 'granted') return false

  const reg = await navigator.serviceWorker.ready
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(
      'BPdli3Hrz20t_-ORRfRnU85sigc4799jxHAWQYwibDENBKiQ0mu6TqztcHQmnhIHZOsrlRD5BSRFqRezkBaHjxs'
    ),
  })
  await api.post('/push/subscribe', sub.toJSON())
  subscribed.value = true
  return true
}

function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

export function usePush() {
  return { supported, permission, subscribed, subscribe }
}
