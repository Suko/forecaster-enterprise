import type { H3Event } from "h3";

type SessionWithAccessToken = { accessToken?: string };

/**
 * Get the JWT access token from the user session
 */
export async function getAccessToken(event: H3Event): Promise<string | null> {
  const session = (await getUserSession(event)) as SessionWithAccessToken | null;
  return session?.accessToken ?? null;
}

/**
 * Make an authenticated request to the FastAPI backend
 * Automatically adds the JWT token from the session
 */
export async function authenticatedFetch<T = unknown>(
  event: H3Event,
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
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
    ...(normalizeHeaders(options.headers) || {}),
  };

  const response = await $fetch<T>(`${apiBaseUrl}${endpoint}`, {
    ...options,
    headers,
  });

  return response;
}

function normalizeHeaders(headers: RequestInit["headers"]): Record<string, string> | undefined {
  if (!headers) return;
  if (headers instanceof Headers) {
    const out: Record<string, string> = {};
    headers.forEach((value, key) => {
      out[key] = value;
    });
    return out;
  }
  if (Array.isArray(headers)) {
    return Object.fromEntries(headers);
  }
  if (typeof headers === "object") {
    return headers as Record<string, string>;
  }
}

/**
 * Validate the JWT token with the backend
 */
export async function validateToken(event: H3Event): Promise<boolean> {
  try {
    await authenticatedFetch(event, "/api/v1/auth/me");
    return true;
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      return false;
    }
    throw error;
  }
}

export function getErrorStatusCode(error: unknown): number | undefined {
  if (typeof error !== "object" || error === null) return;
  const statusCode = (error as { statusCode?: unknown }).statusCode;
  if (typeof statusCode === "number") return statusCode;
  const status = (error as { status?: unknown }).status;
  if (typeof status === "number") return status;
}

export function getErrorMessage(error: unknown): string | undefined {
  if (error instanceof Error) return error.message;
  if (typeof error !== "object" || error === null) return;
  const data = (error as { data?: unknown }).data;
  if (typeof data === "object" && data !== null) {
    const detail = (data as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.length > 0) return detail;
    const dataStatusMessage = (data as { statusMessage?: unknown }).statusMessage;
    if (typeof dataStatusMessage === "string" && dataStatusMessage.length > 0) return dataStatusMessage;
    const dataMessage = (data as { message?: unknown }).message;
    if (typeof dataMessage === "string" && dataMessage.length > 0) return dataMessage;
  }
  const statusMessage = (error as { statusMessage?: unknown }).statusMessage;
  if (typeof statusMessage === "string" && statusMessage.length > 0) return statusMessage;
  const message = (error as { message?: unknown }).message;
  if (typeof message === "string" && message.length > 0) return message;
}
