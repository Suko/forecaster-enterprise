import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../../utils/api";

/**
 * Update purchase order status
 * PUT /api/purchase-orders/:id/status
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const id = event.context.params?.id;
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: "Missing id" });
  }

  try {
    const body = await readBody(event);
    return await authenticatedFetch(
      event,
      `/api/v1/purchase-orders/${encodeURIComponent(id)}/status`,
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
      statusMessage: getErrorMessage(error) || "Failed to update status",
    });
  }
});
