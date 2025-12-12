import type { H3Event } from "h3";

/**
 * Get the JWT access token from the user session
 */
export async function getAccessToken(event: H3Event): Promise<string | null> {
  const session = await getUserSession(event);
  return (session as any)?.accessToken || null;
}

/**
 * Make an authenticated request to the FastAPI backend
 * Automatically adds the JWT token from the session
 */
export async function authenticatedFetch(
  event: H3Event,
  endpoint: string,
  options: RequestInit = {}
): Promise<any> {
  const config = useRuntimeConfig();
  // Use private apiBaseUrl for server-side calls (reaches backend via Docker network)
  const apiBaseUrl = config.apiBaseUrl;

  const token = await getAccessToken(event);

  if (!token) {
    throw createError({
      statusCode: 401,
      statusMessage: "Not authenticated",
    });
  }

  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await $fetch(`${apiBaseUrl}${endpoint}`, {
    ...options,
    headers,
  } as any);

  return response;
}

/**
 * Validate the JWT token with the backend
 */
export async function validateToken(event: H3Event): Promise<boolean> {
  try {
    await authenticatedFetch(event, "/auth/me");
    return true;
  } catch (error: any) {
    if (error.statusCode === 401) {
      return false;
    }
    throw error;
  }
}
