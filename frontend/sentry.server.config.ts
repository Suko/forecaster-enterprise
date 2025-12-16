import * as Sentry from "@sentry/nuxt";

const config = useRuntimeConfig();

Sentry.init({
  dsn: config.public.sentry?.dsn,
  // Adds request headers and IP for users, for more info visit:
  // https://docs.sentry.io/platforms/javascript/guides/nuxt/configuration/options/#sendDefaultPii
  sendDefaultPii: true,
});
