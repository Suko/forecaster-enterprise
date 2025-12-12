import { authenticatedFetch } from "../../../utils/api";

/**
 * Remove a cart item
 * DELETE /api/order-planning/cart/:itemId?supplier_id=...
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
    const endpoint = `/api/v1/order-planning/cart/${encodeURIComponent(itemId)}?supplier_id=${encodeURIComponent(supplierId)}`;
    return await authenticatedFetch(event, endpoint, { method: "DELETE" });
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to remove cart item",
    });
  }
});

