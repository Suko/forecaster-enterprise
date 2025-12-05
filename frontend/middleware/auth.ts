export default defineNuxtRouteMiddleware(async (to) => {
  const { loggedIn, fetch } = useUserSession()

  // Fetch session if not already loaded
  await fetch()

  if (!loggedIn.value) {
    return navigateTo(`/login?redirect=${to.path}`)
  }
})

