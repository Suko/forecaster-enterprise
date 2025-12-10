/**
 * Security event logging utility
 * Logs security-related events for audit purposes
 */

interface SecurityEvent {
  type: 'login_success' | 'login_failure' | 'auth_failure' | 'rate_limit' | 'token_validation_failure' | 'unauthorized_access'
  email?: string
  ip?: string
  userAgent?: string
  details?: Record<string, any>
  timestamp: Date
}

/**
 * Log a security event
 * In production, this should integrate with your logging system (e.g., Winston, Pino, CloudWatch)
 */
export function logSecurityEvent(
  event: Omit<SecurityEvent, 'timestamp'>
): void {
  const securityEvent: SecurityEvent = {
    ...event,
    timestamp: new Date(),
  }

  // In development, log to console with structured format
  // In production, send to your logging service
  if (process.env.NODE_ENV === 'development') {
    console.log('[SECURITY]', JSON.stringify(securityEvent, null, 2))
  } else {
    // TODO: Integrate with production logging service
    // Example: logger.info('security_event', securityEvent)
    // For now, we'll use console but in production you should use a proper logger
    console.log('[SECURITY]', JSON.stringify(securityEvent))
  }
}

/**
 * Extract client IP from request
 */
export function getClientIP(event: any): string {
  // Check various headers for real client IP (when behind proxy)
  const headers = event.node.req.headers
  return (
    headers['x-forwarded-for']?.split(',')[0]?.trim() ||
    headers['x-real-ip'] ||
    event.node.req.socket?.remoteAddress ||
    'unknown'
  )
}

/**
 * Extract user agent from request
 */
export function getUserAgent(event: any): string {
  return event.node.req.headers['user-agent'] || 'unknown'
}








