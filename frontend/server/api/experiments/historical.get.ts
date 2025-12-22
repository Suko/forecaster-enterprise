import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";
import type { HistoricalDataPoint } from "~/types/experiments";

/**
 * Get historical data for an item
 * GET /api/experiments/historical
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const query = getQuery(event);
  const params = new URLSearchParams();

  if (!query.item_id) {
    throw createError({
      statusCode: 400,
      statusMessage: "item_id is required",
    });
  }

  params.append("item_id", String(query.item_id));
  if (query.start_date) params.append("start_date", String(query.start_date));
  if (query.end_date) params.append("end_date", String(query.end_date));

  const url = `/api/v1/forecast/historical?${params.toString()}`;

  try {
    const data = await authenticatedFetch<HistoricalDataPoint[]>(event, url);
    return data;
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) ?? 500,
      statusMessage: getErrorMessage(error) ?? "Failed to fetch historical data",
    });
  }
});

