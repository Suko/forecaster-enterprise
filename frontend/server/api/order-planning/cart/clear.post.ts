import { logger } from "~~/server/utils/logger";
import { authenticatedFetch } from "../../../utils/api";

/**
 * Clear order planning cart
 * POST /api/order-planning/cart/clear
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    return await authenticatedFetch(event, "/api/v1/order-planning/cart/clear", { method: "POST" });
  } catch (error: any) {
    logger.error("Clear cart error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to clear cart",
    });
  }
});
