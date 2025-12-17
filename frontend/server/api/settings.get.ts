import { authenticatedFetch } from "../utils/api";
import type { ClientSettings } from "~/composables/useSettings";

/**
 * Get client settings
 * GET /api/settings
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    return await authenticatedFetch<ClientSettings>(event, `/api/v1/settings`);
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch settings",
    });
  }
});
