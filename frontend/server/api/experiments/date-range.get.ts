import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";
import type { DateRange } from "~/types/experiments";

/**
 * Get date range for historical data
 * GET /api/experiments/date-range
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const query = getQuery(event);
  const params = new URLSearchParams();

  if (query.item_id) {
    params.append("item_id", String(query.item_id));
  }

  const url = `/api/v1/forecast/date-range${params.toString() ? `?${params.toString()}` : ""}`;

  try {
    const dateRange = await authenticatedFetch<DateRange>(event, url);
    return dateRange;
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) ?? 500,
      statusMessage: getErrorMessage(error) ?? "Failed to fetch date range",
    });
  }
});

