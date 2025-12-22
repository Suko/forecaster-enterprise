import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";
import type { CategoryListResponse } from "~/types/experiments";

/**
 * Get product categories
 * GET /api/experiments/categories
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    const response = await authenticatedFetch<CategoryListResponse>(event, "/api/v1/products/categories");
    return response;
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) ?? 500,
      statusMessage: getErrorMessage(error) ?? "Failed to fetch categories",
    });
  }
});

