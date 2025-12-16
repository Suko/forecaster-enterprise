import { authenticatedFetch } from "../../../utils/api";
import { logger } from "~/server/utils/logger";

/**
 * Update a cart item
 * PUT /api/order-planning/cart/:itemId?supplier_id=...
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const itemId = event.context.params?.itemId;
  if (!itemId) {
    throw createError({ statusCode: 400, statusMessage: "Missing itemId" });
  }

  const query = getQuery(event);
  const supplierId = String(query.supplier_id || "");
  if (!supplierId) {
    throw createError({ statusCode: 400, statusMessage: "Missing supplier_id" });
  }

  try {
    const body = await readBody(event);
    const endpoint = `/api/v1/order-planning/cart/${encodeURIComponent(itemId)}?supplier_id=${encodeURIComponent(supplierId)}`;

    return await authenticatedFetch(event, endpoint, { method: "PUT", body });
  } catch (error: any) {
    logger.error("Update cart item error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    // Extract error message from FastAPI response (detail field) or other sources
    const errorMessage =
      error.data?.detail || // FastAPI error detail
      error.data?.statusMessage || // Nuxt error statusMessage
      error.data?.message || // Generic error message
      error.message || // Error object message
      "Failed to update cart item";
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: errorMessage,
      data: error.data, // Preserve original error data
    });
  }
});
