// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui", "nuxt-auth-utils"],
  css: ["~/assets/css/main.css"],
  colorMode: {
    preference: "system", // default to system preference
    fallback: "light", // fallback if system preference not available
    hid: "nuxt-color-mode-script",
    globalName: "__NUXT_COLOR_MODE__",
    componentName: "ColorScheme",
    classPrefix: "",
    classSuffix: "",
    storageKey: "nuxt-color-mode",
  },
  runtimeConfig: {
    // Private keys (only available on server-side)
    // Override at runtime with NUXT_API_BASE_URL env var
    apiBaseUrl: "http://localhost:8000",
    // Public keys (exposed to client-side)
    // Override at runtime with NUXT_PUBLIC_API_BASE_URL env var
    public: {
      apiBaseUrl: "http://localhost:8000",
      demoMode: process.env.NUXT_PUBLIC_DEMO_MODE === 'true',
    },
  },
  // Note: nuxt-auth-utils automatically uses HttpOnly cookies
  // Session cookies are encrypted and secure by default
  // Configure via NUXT_SESSION_PASSWORD environment variable
  // For production, ensure NUXT_SESSION_PASSWORD is set to a strong 32+ character secret
});
