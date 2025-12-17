import { authenticatedFetch } from "../../../utils/api";

/**
 * Update user preferences
 * PUT /api/auth/me/preferences
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const body = await readBody(event);

  try {
    return await authenticatedFetch(event, `/auth/me/preferences`, {
      method: "PUT",
      body,
    });
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to update preferences",
    });
  }
});
