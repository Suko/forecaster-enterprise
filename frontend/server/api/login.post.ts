import { z } from "zod";
import { getErrorMessage, getErrorStatusCode } from "../utils/api";
import { logSecurityEvent, getClientIP, getUserAgent } from "../utils/security-logger";
import { logger } from "../utils/logger";

const bodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export default defineEventHandler(async (event) => {
  const clientIP = getClientIP(event);
  const userAgent = getUserAgent(event);
  let securityLogged = false;
  let attemptedEmail: string | undefined;

  try {
    const { email, password } = await readValidatedBody(event, bodySchema.parse);
    attemptedEmail = email;

    const config = useRuntimeConfig();
    // Use private apiBaseUrl for server-side calls (reaches backend via Docker network)
    const apiBaseUrl = config.apiBaseUrl;

    // Forward to FastAPI backend
    // FastAPI expects OAuth2PasswordRequestForm which uses form data
    const formData = new URLSearchParams();
    formData.append("username", email); // OAuth2 uses 'username' field for email
    formData.append("password", password);

    const response = await $fetch<{ access_token: string }>(`${apiBaseUrl}/api/v1/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });

    if (response?.access_token) {
      const accessToken = response.access_token;

      // Fetch user info from backend using the token
      let userInfo: Record<string, unknown> = { email };
      try {
        const userResponse = await $fetch<Record<string, unknown>>(`${apiBaseUrl}/api/v1/auth/me`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        userInfo = userResponse;
      } catch (err) {
        // If /api/v1/auth/me fails, continue with email only
        logger.warning("Failed to fetch user info", { error: err });
      }

      // Store token and user info in session using nuxt-auth-utils
      await setUserSession(event, {
        user: userInfo,
        accessToken: accessToken,
      });

      // Log successful login
      logSecurityEvent({
        type: "login_success",
        email: email,
        ip: clientIP,
        userAgent: userAgent,
      });
      securityLogged = true;

      return {};
    }

    // Log failed login attempt
    logSecurityEvent({
      type: "login_failure",
      ip: clientIP,
      userAgent: userAgent,
      details: { reason: "Invalid credentials or no token received" },
    });
    securityLogged = true;

    throw createError({
      statusCode: 401,
      statusMessage: "Authentication failed",
    });
  } catch (error: unknown) {
    const statusCode = getErrorStatusCode(error);
    const errorMessage = getErrorMessage(error);

    // Log security events for authentication failures (only if not already logged)
    if (!securityLogged && (statusCode === 401 || statusCode === 429)) {
      logSecurityEvent({
        type: statusCode === 429 ? "rate_limit" : "login_failure",
        email: attemptedEmail,
        ip: clientIP,
        userAgent: userAgent,
        details: {
          statusCode,
          message: errorMessage,
        },
      });
    }

    // Re-throw if it's already a proper error with status code
    if (statusCode) {
      throw error;
    }

    // Generic error response
    throw createError({
      statusCode: 500,
      statusMessage: "Internal server error",
    });
  }
});
