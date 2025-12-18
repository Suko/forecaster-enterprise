import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../utils/api";
import type { ClientSettings } from "~/composables/useSettings";

/**
 * Get client settings
 * GET /api/settings
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    return await authenticatedFetch<ClientSettings>(event, "/api/v1/settings");
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to fetch settings",
    });
  }
});
