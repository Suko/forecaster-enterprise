/**
 * Demo Mode Plugin
 * Initializes demo mode on app startup
 * Auto-logs in user and sets up demo environment
 * 
 * This plugin runs early to ensure demo auth is set up before other plugins/middleware
 */

export default defineNuxtPlugin({
  name: 'demo-mode',
  enforce: 'pre', // Run before other plugins
  async setup() {
    const { isDemoMode } = useDemoMode();
    
    // Check if demo mode is enabled
    if (isDemoMode.value) {
      const { initDemoAuth } = useDemoAuth();
      
      // Auto-login with demo user
      await initDemoAuth();
      
      // If on login page, redirect to dashboard
      if (typeof window !== 'undefined' && window.location.pathname === '/login') {
        await navigateTo('/dashboard');
      }
    }
  }
});

