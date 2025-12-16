/**
 * Demo Authentication Composable
 * Bypasses authentication for demo mode
 * Auto-logs in with a demo user
 */

export const useDemoAuth = () => {
  const { user, fetch: refreshSession } = useUserSession();
  
  /**
   * Auto-login with demo user
   * In demo mode, we bypass the real auth and set a demo session cookie
   */
  const loginDemo = async () => {
    // For demo mode, call the login API with demo credentials
    // The backend should accept demo credentials when in demo mode
    try {
      if (typeof window !== 'undefined') {
        // Call login API with demo credentials
        // The server will handle setting the session cookie
        await $fetch('/api/login', {
          method: 'POST',
          body: {
            email: 'demo@forecaster-enterprise.com',
            password: 'demo', // Demo password
          },
        });
        
        // Refresh session to get user data
        await refreshSession();
      }
    } catch (err) {
      // If login fails, try to set demo session manually
      console.warn('Demo login failed, using fallback:', err);
      // Fallback: Set demo session in localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('demo-session', JSON.stringify({
          user: {
            email: "demo@forecaster-enterprise.com",
            name: "Demo User",
            role: "admin",
          },
          accessToken: "demo-token",
        }));
      }
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

