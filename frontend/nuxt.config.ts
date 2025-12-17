// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  modules: ["@nuxt/ui", "nuxt-auth-utils", "@sentry/nuxt/module"],
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
    },
  },

  sentry: {
    org: "forecaster-4b",
    project: "forecast-frontend",
  },
});
