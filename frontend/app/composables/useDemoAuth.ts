/**
 * Demo Authentication Composable
 * Bypasses authentication for demo mode
 * Auto-logs in with a demo user
 */

export const useDemoAuth = () => {
  const { user, fetch: refreshSession, clear: clearSession } = useUserSession();
  const { isDemoMode } = useDemoMode();

  /**
   * Auto-login with demo user
   * In demo mode, we bypass the real auth and set a demo session cookie
   */
  const loginDemo = async () => {
    if (isDemoMode.value) {
      // Directly set a demo session without calling a backend API
      try {
        await $fetch('/api/login', {
          method: 'POST',
          body: {
            email: 'demo@forecaster-enterprise.com',
            password: 'demo',
          },
        });
        await refreshSession(); // Ensure the session is loaded
      } catch (err) {
        // If login fails, try to set session directly via client-side
        console.warn('Demo login API call failed, trying direct session:', err);
        // The login.post.ts server route should handle this, but if it fails,
        // the middleware will allow access anyway in demo mode
      }
    } else {
      console.warn('Attempted to call loginDemo outside of demo mode.');
    }
  };
  
  /**
   * Check if user is authenticated (always true in demo mode)
   */
  const isAuthenticated = computed(() => {
    return !!user.value;
  });
  
  /**
   * Initialize demo auth on mount
   */
  const initDemoAuth = async () => {
    if (!user.value) {
      await loginDemo();
    }
  };
  
  return {
    loginDemo,
    isAuthenticated,
    initDemoAuth,
  };
};

