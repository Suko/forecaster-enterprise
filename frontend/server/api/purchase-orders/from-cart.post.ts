import { logger } from "~~/server/utils/logger";
import { authenticatedFetch } from "../../utils/api";

/**
 * Create a purchase order from cart items
 * POST /api/purchase-orders/from-cart
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    const body = await readBody(event);

    const supplierId = String(body?.supplier_id || "");
    if (!supplierId) {
      throw createError({ statusCode: 400, statusMessage: "Missing supplier_id" });
    }

    const qs = new URLSearchParams(
      Object.entries({
        supplier_id: supplierId,
        shipping_method: body?.shipping_method,
        shipping_unit: body?.shipping_unit,
        notes: body?.notes,
      })
        .filter(([, v]) => v !== undefined && v !== null && String(v) !== "")
        .map(([k, v]) => [k, String(v)])
    ).toString();

    return await authenticatedFetch(event, `/api/v1/purchase-orders/from-cart?${qs}`, {
      method: "POST",
    });
  } catch (error: any) {
    logger.error("Create purchase order from cart error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to create purchase order",
    });
  }
});
