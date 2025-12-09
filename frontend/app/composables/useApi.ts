/**
 * Composable for making authenticated API calls to the backend
 * Uses Nuxt server routes which handle JWT tokens automatically
 */
export const useApi = () => {
  const { user } = useUserSession()

  /**
   * Make an authenticated API call through Nuxt server routes
   */
  const apiCall = async <T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> => {
    if (!user.value) {
      throw new Error('Not authenticated')
    }

    // All API calls go through Nuxt server routes
    // Server routes will handle adding JWT tokens
    const response = await $fetch<T>(`/api${endpoint}`, {
      ...options,
      credentials: 'include', // Include session cookie
    })

    return response
  }

  return {
    apiCall,
  }
}





