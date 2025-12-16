import * as Sentry from "@sentry/nuxt";
import { logger } from "./logger";

/**
 * Security event logging utility
 * Logs security-related events for audit purposes and Sentry monitoring
 */

interface SecurityEvent {
  type:
    | "login_success"
    | "login_failure"
    | "auth_failure"
    | "rate_limit"
    | "token_validation_failure"
    | "unauthorized_access";
  email?: string;
  ip?: string;
  userAgent?: string;
  details?: Record<string, any>;
  timestamp: Date;
}

/**
 * Get log level based on event type
 */
function getLogLevel(eventType: SecurityEvent["type"]): "info" | "warning" | "error" {
  switch (eventType) {
    case "unauthorized_access":
    case "auth_failure":
      return "error";
    case "login_failure":
    case "rate_limit":
    case "token_validation_failure":
      return "warning";
    case "login_success":
      return "info";
    default:
      return "info";
  }
}

/**
 * Log a security event
 * Uses centralized logger for consistent dev/prod behavior
 */
export function logSecurityEvent(event: Omit<SecurityEvent, "timestamp">): void {
  const securityEvent: SecurityEvent = {
    ...event,
    timestamp: new Date(),
  };

  const logLevel = getLogLevel(event.type);

  // Log using centralized logger (handles dev vs prod automatically)
  logger[logLevel](`Security Event: ${event.type}`, {
    event_type: event.type,
    email: event.email,
    ip: event.ip,
    userAgent: event.userAgent,
    timestamp: securityEvent.timestamp.toISOString(),
    ...event.details,
  });

  // Additional Sentry context for security events (production only)
  if (process.env.NODE_ENV !== "development") {
    try {
      // Set user context if email is available
      if (event.email) {
        Sentry.setUser({
          email: event.email,
          ip_address: event.ip,
        });
      }

      // Capture security failures with fingerprinting for grouping
      if (
        event.type === "login_failure" ||
        event.type === "auth_failure" ||
        event.type === "unauthorized_access" ||
        event.type === "rate_limit" ||
        event.type === "token_validation_failure"
      ) {
        Sentry.captureMessage(`Security Event: ${event.type}`, {
          level: logLevel === "error" ? "error" : "warning",
          contexts: {
            security: {
              event_type: event.type,
              ip: event.ip,
              userAgent: event.userAgent,
              timestamp: securityEvent.timestamp.toISOString(),
            },
          },
          tags: {
            security_event: event.type,
          },
          extra: {
            ...event.details,
            full_event: securityEvent,
          },
          // Fingerprint for grouping similar events
          fingerprint: ["security-event", event.type, event.email || "anonymous"],
        });
      }
    } catch (err) {
      console.error("Failed to send security event to Sentry:", err);
    }
  }
}

/**
 * Extract client IP from request
 */
export function getClientIP(event: any): string {
  // Check various headers for real client IP (when behind proxy)
  const headers = event.node.req.headers;
  return (
    headers["x-forwarded-for"]?.split(",")[0]?.trim() ||
    headers["x-real-ip"] ||
    event.node.req.socket?.remoteAddress ||
    "unknown"
  );
}

/**
 * Extract user agent from request
 */
export function getUserAgent(event: any): string {
  return event.node.req.headers["user-agent"] || "unknown";
}
