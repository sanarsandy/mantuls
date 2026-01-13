export default defineNuxtRouteMiddleware((to, from) => {
  const tokenCookie = useCookie('ocr_token')

  // If not authenticated and trying to access protected route
  if (to.path !== '/login') {
    if (!tokenCookie.value) {
      return navigateTo('/login')
    }
  }
})
