export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn } = useUserSession()

  // redirect the user to the login screen if they're not authenticated
  if (!loggedIn.value) {
    // Preserve the intended destination for redirect after login
    return navigateTo({
      path: '/login',
      query: { returnTo: to.fullPath }
    })
  }
})

