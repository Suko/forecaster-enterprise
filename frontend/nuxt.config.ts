// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },
  modules: [
    'nuxt-auth-utils',
    '@nuxtjs/tailwindcss'
  ],
  runtimeConfig: {
    // Private keys (only available on server-side)
    apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
    // Public keys (exposed to client-side)
    public: {
      apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000'
    }
  },
  auth: {
    // Session configuration
    session: {
      maxAge: 60 * 60 * 24 * 7 // 1 week
    }
  },
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },
})

