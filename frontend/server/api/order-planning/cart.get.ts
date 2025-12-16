import { authenticatedFetch } from "../../utils/api";
import { logger } from "~/server/utils/logger";

/**
 * Get order planning cart
 * GET /api/order-planning/cart
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    return await authenticatedFetch(event, "/api/v1/order-planning/cart");
  } catch (error: any) {
    logger.error("Fetch cart error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch cart",
    });
  }
});
