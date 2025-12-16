import * as Sentry from "@sentry/nuxt";

const config = useRuntimeConfig();
Sentry.init({
  dsn: "https://807db02f3d58f65c7caf28b0f074c0b4@o1296949.ingest.us.sentry.io/4510544006348800",

  // We recommend adjusting this value in production, or using tracesSampler
  // for finer control
  tracesSampleRate: 1.0,

  // Enable logs to be sent to Sentry
  enableLogs: true,

  // Enable sending of user PII (Personally Identifiable Information)
  // https://docs.sentry.io/platforms/javascript/guides/nuxt/configuration/options/#sendDefaultPii
  sendDefaultPii: true,

  // Setting this option to true will print useful information to the console while you're setting up Sentry.
  debug: false,
});
