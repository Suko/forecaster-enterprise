/**
 * Composable for handling authentication errors
 * Automatically redirects to login on 401 errors
 */
export const useAuthError = () => {
  const { clear } = useUserSession()
  const route = useRoute()

  /**
   * Handle API errors and redirect to login if 401
   * @returns true if error was a 401 and was handled, false otherwise
   */
  const handleAuthError = async (error: any): Promise<boolean> => {
    // Check if it's a 401 Unauthorized error
    if (error?.statusCode === 401 || error?.status === 401 || error?.response?.status === 401) {
      // Clear session
      await clear()
      
      // Redirect to login with return URL
      const returnTo = route.fullPath !== '/login' ? route.fullPath : undefined
      await navigateTo({
        path: '/login',
        query: returnTo ? { returnTo } : undefined
      })
      
      return true // Indicates error was handled
    }
    return false // Error was not a 401
  }

  return {
    handleAuthError,
  }
}

