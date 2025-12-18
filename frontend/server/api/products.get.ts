import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../utils/api";
import type { ProductListResponse } from "~/types/product";

/**
 * Fetch products from backend
 * GET /api/products
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

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
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) ?? 500,
      statusMessage: getErrorMessage(error) ?? "Failed to fetch products",
    });
  }
});
