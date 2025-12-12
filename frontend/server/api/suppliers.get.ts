import { authenticatedFetch } from "../utils/api";
import type { SupplierListResponse } from "~/types/supplier";

/**
 * Fetch suppliers from backend
 * GET /api/suppliers
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    const query = getQuery(event);
    const queryString = new URLSearchParams(
      Object.entries(query)
        .filter(([, v]) => v !== undefined && v !== null && String(v) !== "")
        .map(([k, v]) => [k, String(v)])
    ).toString();

    return await authenticatedFetch<SupplierListResponse>(
      event,
      `/api/v1/suppliers${queryString ? `?${queryString}` : ""}`
    );
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch suppliers",
    });
  }
});

