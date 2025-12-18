import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";

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
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to create purchase order",
    });
  }
});
