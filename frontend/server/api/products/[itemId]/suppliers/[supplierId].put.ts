import { logger } from "~~/server/utils/logger";
import { authenticatedFetch } from "../../../../utils/api";

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
  } catch (error: any) {
    logger.error("Update product-supplier conditions error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    // Extract error message from FastAPI response
    const errorMessage =
      error.data?.detail ||
      error.data?.statusMessage ||
      error.data?.message ||
      error.message ||
      "Failed to update product-supplier condition";
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: errorMessage,
      data: error.data,
    });
  }
});
