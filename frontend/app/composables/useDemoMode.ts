/**
 * Demo Mode Detection
 * Checks if the app should run in demo mode (static data, no backend)
 */

export const useDemoMode = () => {
  const config = useRuntimeConfig();
  
  // Check if demo mode is enabled via environment variable or URL parameter
  const isDemoMode = computed(() => {
    // Check runtime config (set by NUXT_PUBLIC_DEMO_MODE env var)
    if (config.public.demoMode === true) {
      return true;
    }
    
    // Check environment variable (fallback)
    if (import.meta.env.NUXT_PUBLIC_DEMO_MODE === 'true') {
      return true;
    }
    
    // Check URL parameter (for testing)
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('demo') === 'true') {
        return true;
      }
    }
    
    return false;
  });
  
  return {
    isDemoMode,
  };
};

