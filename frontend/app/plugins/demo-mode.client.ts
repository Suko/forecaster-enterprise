/**
 * Demo Mode Plugin
 * Initializes demo mode on app startup
 * Auto-logs in user and sets up demo environment
 */

export default defineNuxtPlugin(async () => {
  const { isDemoMode } = useDemoMode();
  const { initDemoAuth } = useDemoAuth();
  
  // Check if demo mode is enabled
  if (isDemoMode.value) {
    // Auto-login with demo user
    await initDemoAuth();
    
    // Demo banner removed per user request
  }
});

