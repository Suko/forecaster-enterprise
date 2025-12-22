import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../../utils/api";
import type { QualityResponse } from "~/types/experiments";

/**
 * Get quality metrics for an item
 * GET /api/experiments/quality/:itemId
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const itemId = getRouterParam(event, "itemId");
  if (!itemId) {
    throw createError({
      statusCode: 400,
      statusMessage: "itemId is required",
    });
  }

  const query = getQuery(event);
  const params = new URLSearchParams();

  if (query.start_date) params.append("start_date", String(query.start_date));
  if (query.end_date) params.append("end_date", String(query.end_date));

  const url = `/api/v1/forecasts/quality/${encodeURIComponent(itemId)}${params.toString() ? `?${params.toString()}` : ""}`;

  try {
    const response = await authenticatedFetch<QualityResponse>(event, url);
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
      statusMessage: getErrorMessage(error) ?? "Failed to fetch quality metrics",
    });
  }
});

