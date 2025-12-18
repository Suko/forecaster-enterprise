import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../../utils/api";

/**
 * Update user preferences
 * PUT /api/auth/me/preferences
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const body = await readBody(event);

  try {
    return await authenticatedFetch(event, "/api/v1/auth/me/preferences", {
      method: "PUT",
      body,
    });
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to update preferences",
    });
  }
});
