import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../utils/api";

/**
 * List purchase orders
 * GET /api/purchase-orders
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    const query = getQuery(event);
    const qs = new URLSearchParams(
      Object.entries(query)
        .filter(([, v]) => v !== undefined && v !== null && String(v) !== "")
        .map(([k, v]) => [k, String(v)])
    ).toString();

    return await authenticatedFetch(event, `/api/v1/purchase-orders${qs ? `?${qs}` : ""}`);
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to fetch purchase orders",
    });
  }
});
