import { logger } from "~~/server/utils/logger";
import { authenticatedFetch } from "../../utils/api";

/**
 * Get purchase order detail
 * GET /api/purchase-orders/:id
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const id = event.context.params?.id;
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: "Missing id" });
  }

  try {
    return await authenticatedFetch(event, `/api/v1/purchase-orders/${encodeURIComponent(id)}`);
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch purchase order",
    });
  }
});
