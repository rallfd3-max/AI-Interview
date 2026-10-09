import Vue from 'vue'
import VueRouter from 'vue-router'
import Login from '../pages/login.vue'
import { isAuthenticated } from './apis/auth.js'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    redirect: '/home'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/home',
    name: 'Home',
    component: () => import('../pages/home.vue'),
    meta: { requiresAuth: true }
  }
]

const router = new VueRouter({
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 检查页面是否需要认证
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // 检查用户是否已登录
    if (!isAuthenticated()) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }  // 保存要跳转的页面路径
      })
    } else {
      next()
    }
  } else {
    // 如果是登录页面且用户已登录，重定向到首页
    if (to.path === '/login' && isAuthenticated()) {
      next('/home')
    } else {
      next()
    }
  }
})

export default router
