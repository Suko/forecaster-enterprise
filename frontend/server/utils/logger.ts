import * as Sentry from "@sentry/nuxt";

/**
 * Centralized logging utility
 * Routes logs to console in development, Sentry in production
 */

export type LogLevel = "debug" | "info" | "warning" | "error";

interface LogContext {
  [key: string]: any;
}

// Machine ID cache - set by license-status endpoint
let cachedMachineId: string | null = null;

/**
 * Set the machine ID (called by license-status endpoint)
 */
export function setMachineId(machineId: string | null): void {
  cachedMachineId = machineId;
}

/**
 * Get the cached machine ID
 */
export function getMachineId(): string | null {
  return cachedMachineId;
}

/**
 * Log a message with appropriate level
 * Development: Console output
 * Production: Sentry capture
 */
export function log(
  level: LogLevel,
  message: string,
  context?: LogContext,
  error?: Error | unknown
): void {
  const isDevelopment = process.env.NODE_ENV === "development";
  const timestamp = new Date().toISOString();
  const machineId = getMachineId();

  // Enrich context with machine ID if available
  const enrichedContext: LogContext = {
    ...(machineId && { machineId }),
    ...context,
  };

  // Always log to console for server logs
  const logPrefix = machineId
    ? `[${timestamp}] [${level.toUpperCase()}] [${machineId}]`
    : `[${timestamp}] [${level.toUpperCase()}]`;
  const logMessage =
    Object.keys(enrichedContext).length > 0
      ? `${logPrefix} ${message}\n${JSON.stringify(enrichedContext, null, 2)}`
      : `${logPrefix} ${message}`;

  if (isDevelopment) {
    // Detailed console output in development
    switch (level) {
      case "debug":
        console.debug(logMessage, error || "");
        break;
      case "info":
        console.info(logMessage, error || "");
        break;
      case "warning":
        console.warn(logMessage, error || "");
        break;
      case "error":
        console.error(logMessage, error || "");
        break;
    }
  } else {
    // Production: console + Sentry
    console.log(logMessage);

    // Send to Sentry based on level
    try {
      const sentryLevel = getSentryLevel(level);

      // Add breadcrumb for all logs
      Sentry.addBreadcrumb({
        message,
        level: sentryLevel,
        data: enrichedContext,
        timestamp: Date.now() / 1000,
      });

      // Capture warnings and errors in Sentry
      if (level === "warning" || level === "error") {
        if (error instanceof Error) {
          // Capture actual errors with stack traces
          Sentry.captureException(error, {
            level: sentryLevel,
            contexts: {
              log: enrichedContext,
            },
            tags: {
              log_level: level,
              ...(machineId && { machine_id: machineId }),
            },
          });
        } else {
          // Use Sentry.logger for structured logging
          const attributes = { ...enrichedContext, error };
          if (level === "warning") {
            Sentry.logger.warn(message, attributes);
          } else {
            Sentry.logger.error(message, attributes);
          }
        }
      } else if (level === "info") {
        Sentry.logger.info(message, enrichedContext);
      } else if (level === "debug") {
        Sentry.logger.debug(message, enrichedContext);
      }
    } catch (err) {
      console.error("Failed to send log to Sentry:", err);
    }
  }
}

/**
 * Map log level to Sentry severity
 */
function getSentryLevel(level: LogLevel): Sentry.SeverityLevel {
  switch (level) {
    case "debug":
      return "debug";
    case "info":
      return "info";
    case "warning":
      return "warning";
    case "error":
      return "error";
    default:
      return "info";
  }
}

/**
 * Convenience methods for common log levels
 */
export const logger = {
  debug: (message: string, context?: LogContext) => log("debug", message, context),
  info: (message: string, context?: LogContext) => log("info", message, context),
  warning: (message: string, context?: LogContext, error?: Error | unknown) =>
    log("warning", message, context, error),
  error: (message: string, context?: LogContext, error?: Error | unknown) =>
    log("error", message, context, error),
};
