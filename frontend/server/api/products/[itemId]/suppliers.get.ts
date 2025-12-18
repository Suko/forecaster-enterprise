import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../../utils/api";

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
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to get product suppliers",
    });
  }
});
