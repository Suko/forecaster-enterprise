import { authenticatedFetch } from "../utils/api";
import { logSecurityEvent, getClientIP, getUserAgent } from "../utils/security-logger";

/**
 * Get current authenticated user information from backend
 * Protected route - requires user session
 */
export default defineEventHandler(async (event) => {
  const clientIP = getClientIP(event);
  const userAgent = getUserAgent(event);

  // Make sure the user is logged in
  // This will throw a 401 error if the request doesn't come from a valid user session
  const { user } = await requireUserSession(event);

  try {
    // Fetch latest user info from backend
    const userInfo = await authenticatedFetch(event, "/auth/me");

    // Update session with latest user info
    await setUserSession(event, {
      user: userInfo,
      accessToken: ((await getUserSession(event)) as any)?.accessToken,
    });

    return userInfo;
  } catch (error: any) {
    if (error.statusCode === 401) {
      // Log token validation failure
      logSecurityEvent({
        type: "token_validation_failure",
        email: (user as any)?.email,
        ip: clientIP,
        userAgent: userAgent,
        details: { reason: "Token invalid or expired" },
      });

      // Token is invalid, clear session
      await clearUserSession(event);
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw error;
  }
});
