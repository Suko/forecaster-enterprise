export default defineNuxtRouteMiddleware((to) => {
  // Skip auth check if page explicitly sets auth: false
  if (to.meta.auth === false) {
    return;
  }

  const { loggedIn } = useUserSession();

  // Redirect the user to the login screen if they're not authenticated
  if (!loggedIn.value) {
    // Preserve the intended destination for redirect after login
    return navigateTo({
      path: "/login",
      query: { returnTo: to.fullPath },
    });
  }
});
