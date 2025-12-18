import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../../utils/api";

/**
 * Add item to order planning cart
 * POST /api/order-planning/cart/add
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    const body = await readBody(event);

    const result = await authenticatedFetch(event, "/api/v1/order-planning/cart/add", {
      method: "POST",
      body,
    });

    return result;
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) ?? 500,
      statusMessage: getErrorMessage(error) ?? "Failed to add item to cart",
    });
  }
});
