import { authenticatedFetch } from "../utils/api";
import type { ProductListResponse } from "~/types/product";

/**
 * Fetch products from backend
 * GET /api/products
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event);

  try {
    const query = getQuery(event);
    const queryString = new URLSearchParams(
      Object.entries(query)
        .filter(([_, v]) => v !== undefined && v !== null && v !== "")
        .map(([k, v]) => [k, String(v)])
    ).toString();

    const products = await authenticatedFetch<ProductListResponse>(
      event,
      `/api/v1/products${queryString ? `?${queryString}` : ""}`
    );

    return products;
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch products",
    });
  }
});
