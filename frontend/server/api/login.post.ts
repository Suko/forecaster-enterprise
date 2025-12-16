import { z } from "zod";
import { logSecurityEvent, getClientIP, getUserAgent } from "../utils/security-logger";
import { logger } from "../utils/logger";

const bodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

export default defineEventHandler(async (event) => {
  const clientIP = getClientIP(event);
  const userAgent = getUserAgent(event);

  try {
    const { email, password } = await readValidatedBody(event, bodySchema.parse);

    const config = useRuntimeConfig();
    // Use private apiBaseUrl for server-side calls (reaches backend via Docker network)
    const apiBaseUrl = config.apiBaseUrl;

    // Forward to FastAPI backend
    // FastAPI expects OAuth2PasswordRequestForm which uses form data
    const formData = new URLSearchParams();
    formData.append("username", email); // OAuth2 uses 'username' field for email
    formData.append("password", password);

    const response = await $fetch(`${apiBaseUrl}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData.toString(),
    });

    if (
      response &&
      typeof response === "object" &&
      response !== null &&
      "access_token" in response
    ) {
      const accessToken = (response as any).access_token;

      // Fetch user info from backend using the token
      let userInfo = { email };
      try {
        const userResponse = await $fetch(`${apiBaseUrl}/auth/me`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });
        userInfo = userResponse as any;
      } catch (err) {
        // If /auth/me fails, continue with email only
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

      return {};
    }

    // Log failed login attempt
    logSecurityEvent({
      type: "login_failure",
      ip: clientIP,
      userAgent: userAgent,
      details: { reason: "Invalid credentials or no token received" },
    });

    throw createError({
      statusCode: 401,
      statusMessage: "Authentication failed",
    });
  } catch (error: unknown) {
    // Type-safe error handling
    const statusCode =
      error && typeof error === "object" && "statusCode" in error
        ? (error as any).statusCode
        : undefined;
    const errorData =
      error && typeof error === "object" && "data" in error ? (error as any).data : undefined;
    const errorMessage =
      error && typeof error === "object" && "statusMessage" in error
        ? (error as any).statusMessage
        : undefined;

    // Log security events for authentication failures
    if (statusCode === 401 || statusCode === 429) {
      logSecurityEvent({
        type: statusCode === 429 ? "rate_limit" : "login_failure",
        email: errorData?.email,
        ip: clientIP,
        userAgent: userAgent,
        details: {
          statusCode,
          message: errorData?.detail || errorMessage,
        },
      });
    }

    // Re-throw if it's already a proper error with status code
    if (statusCode) {
      throw error;
    }

    // Handle FastAPI error responses
    if (errorData) {
      throw createError({
        statusCode: statusCode || 401,
        statusMessage: errorData?.detail || "Login failed",
        data: errorData,
      });
    }

    // Log unexpected errors for debugging
    logger.error("Unexpected login error", { error });

    // Generic error response
    throw createError({
      statusCode: 500,
      statusMessage: "Internal server error",
    });
  }
});
