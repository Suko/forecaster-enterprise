import { authenticatedFetch } from "../utils/api";

/**
 * Example: Protected server route that makes authenticated requests to backend
 * This demonstrates how to use the authenticatedFetch utility
 */
export default defineEventHandler(async (event) => {
  // Make sure the user is logged in
  // This will throw a 401 error if the request doesn't come from a valid user session
  const { user } = await requireUserSession(event);

  try {
    // Make authenticated request to backend
    // The JWT token is automatically added from the session
    const userInfo = await authenticatedFetch(event, "/auth/me");
    
    return {
      message: "This is a protected route",
      user: userInfo,
    };
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw error;
  }
});

