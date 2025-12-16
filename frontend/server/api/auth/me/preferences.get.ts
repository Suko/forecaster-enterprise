import { logger } from "~~/server/utils/logger";
import { authenticatedFetch } from "../../../utils/api";

/**
 * Get user preferences
 * GET /api/auth/me/preferences
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    return await authenticatedFetch(event, `/auth/me/preferences`);
  } catch (error: any) {
    logger.error("Fetch user preferences error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch preferences",
    });
  }
});
