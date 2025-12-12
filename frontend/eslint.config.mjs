import js from "@eslint/js";
import vue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";
import * as parserVue from "vue-eslint-parser";
import globals from "globals";

export default tseslint.config(
  {
    ignores: [".nuxt/**", ".output/**", "node_modules/**", "dist/**"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{js,mjs,cjs,ts}"],
    languageOptions: {
      parser: tseslint.parser,
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      quotes: ["error", "double", { avoidEscape: true }],
      semi: ["error", "always"],
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn", // Make it a warning instead of error
      "no-undef": "off", // TypeScript handles this
    },
  },
  {
    files: ["**/*.vue"],
    languageOptions: {
      parser: parserVue,
      parserOptions: {
        parser: tseslint.parser,
        ecmaVersion: "latest",
        sourceType: "module",
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        // Nuxt auto-imports (these are available globally in Nuxt)
        definePageMeta: "readonly",
        navigateTo: "readonly",
        useRoute: "readonly",
        useRouter: "readonly",
        useHead: "readonly",
        useSeoMeta: "readonly",
        useCookie: "readonly",
        useRequestHeaders: "readonly",
        useRequestEvent: "readonly",
        useRequestURL: "readonly",
        useRuntimeConfig: "readonly",
        useState: "readonly",
        // Vue composables
        ref: "readonly",
        computed: "readonly",
        watch: "readonly",
        watchEffect: "readonly",
        reactive: "readonly",
        readonly: "readonly",
        onMounted: "readonly",
        onUnmounted: "readonly",
        onBeforeMount: "readonly",
        onBeforeUnmount: "readonly",
        onUpdated: "readonly",
        onBeforeUpdate: "readonly",
        nextTick: "readonly",
        // Nuxt composables (common ones)
        useUserSession: "readonly",
        useApi: "readonly",
        useAuthError: "readonly",
        useToast: "readonly",
        useAgGridProducts: "readonly",
        useRecommendations: "readonly",
      },
    },
    plugins: {
      vue,
    },
    rules: {
      ...vue.configs["flat/recommended"].rules,
      // Enforce consistent quote style (double quotes)
      quotes: ["error", "double", { avoidEscape: true }],
      // Enforce semicolons
      semi: ["error", "always"],
      // Vue specific - relaxed rules
      "vue/multi-word-component-names": "off",
      "vue/no-v-html": "off",
      "vue/singleline-html-element-content-newline": "off",
      "vue/max-attributes-per-line": "off",
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "warn", // Make it a warning instead of error
      "no-undef": "off", // TypeScript handles this
    },
  }
);
