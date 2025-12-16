import { authenticatedFetch } from "../../../utils/api";
import { logger } from "~/server/utils/logger";

/**
 * Add item to order planning cart
 * POST /api/order-planning/cart/add
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event);

  try {
    const body = await readBody(event);

    const result = await authenticatedFetch(event, "/api/v1/order-planning/cart/add", {
      method: "POST",
      body,
    });

    return result;
  } catch (error: any) {
    logger.error("Add to cart error", { error });
    if (error.statusCode === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to add item to cart",
    });
  }
});
