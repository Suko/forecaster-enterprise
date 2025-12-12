/**
 * Security headers middleware
 * Adds security headers to all responses
 */
export default defineEventHandler((event) => {
  // Security headers
  setHeader(event, "X-Content-Type-Options", "nosniff");
  setHeader(event, "X-Frame-Options", "DENY");
  setHeader(event, "X-XSS-Protection", "1; mode=block");
  setHeader(event, "Referrer-Policy", "strict-origin-when-cross-origin");

  // Only add HSTS in production (HTTPS required)
  const isProduction = process.env.NODE_ENV === "production";
  if (isProduction) {
    setHeader(event, "Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload");
  }

  // Content Security Policy
  // Adjust based on your needs - this is a restrictive default
  setHeader(
    event,
    "Content-Security-Policy",
    [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Required for Nuxt/Vue in dev
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "frame-ancestors 'none'",
    ].join("; ")
  );

  // Permissions Policy (formerly Feature Policy)
  setHeader(
    event,
    "Permissions-Policy",
    ["geolocation=()", "microphone=()", "camera=()"].join(", ")
  );
});
