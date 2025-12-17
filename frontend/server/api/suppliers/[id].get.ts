import { authenticatedFetch } from "../../utils/api";
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
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch supplier",
    });
  }
});
