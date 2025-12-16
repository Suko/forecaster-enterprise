import { logger } from "~~/server/utils/logger";
import { authenticatedFetch } from "../../../utils/api";

/**
 * Get all suppliers for a product with conditions (MOQ, lead time, etc.)
 * GET /api/products/:itemId/suppliers
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const itemId = event.context.params?.itemId;
  if (!itemId) {
    throw createError({ statusCode: 400, statusMessage: "Missing itemId" });
  }

  try {
    return await authenticatedFetch(
      event,
      `/api/v1/products/${encodeURIComponent(itemId)}/suppliers`,
      {
        method: "GET",
      }
    );
  } catch (error: any) {
    logger.error("Fetch product suppliers error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to get product suppliers",
    });
  }
});
