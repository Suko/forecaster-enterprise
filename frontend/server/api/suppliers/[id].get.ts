import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";
import type { Supplier } from "~/types/supplier";

/**
 * Fetch supplier detail from backend
 * GET /api/suppliers/:id
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const id = event.context.params?.id;
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: "Missing id" });
  }

  try {
    return await authenticatedFetch<Supplier>(event, `/api/v1/suppliers/${encodeURIComponent(id)}`);
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to fetch supplier",
    });
  }
});
