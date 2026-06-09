import { createRouter, createWebHistory } from 'vue-router'
import { api } from '../api/client'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { guest: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue'),
      meta: { guest: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/alerts',
      name: 'alerts',
      component: () => import('../views/AlertsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/add',
      name: 'add',
      component: () => import('../views/AddItemView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/item/:id',
      name: 'item-detail',
      component: () => import('../views/ItemDetailView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/SettingsView.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach(async (to, _from) => {
  if (to.meta.requiresAuth) {
    try {
      await api.get('/me')
    } catch {
      return { name: 'login' }
    }
  }
  if (to.meta.guest) {
    try {
      await api.get('/me')
      return { name: 'dashboard' }
    } catch {
      /* stay on guest page */
    }
  }
})

export default router
