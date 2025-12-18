import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../../../utils/api";

/**
 * Update product-supplier conditions (MOQ, lead time, packaging)
 * PUT /api/products/:itemId/suppliers/:supplierId
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const itemId = event.context.params?.itemId;
  const supplierId = event.context.params?.supplierId;

  if (!itemId) {
    throw createError({ statusCode: 400, statusMessage: "Missing itemId" });
  }
  if (!supplierId) {
    throw createError({ statusCode: 400, statusMessage: "Missing supplierId" });
  }

  const body = await readBody(event);

  try {
    return await authenticatedFetch(
      event,
      `/api/v1/products/${encodeURIComponent(itemId)}/suppliers/${encodeURIComponent(supplierId)}`,
      {
        method: "PUT",
        body,
      }
    );
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to update product-supplier condition",
    });
  }
});
