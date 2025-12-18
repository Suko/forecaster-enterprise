import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";

/**
 * Get order planning cart
 * GET /api/order-planning/cart
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    return await authenticatedFetch(event, "/api/v1/order-planning/cart");
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to fetch cart",
    });
  }
});
