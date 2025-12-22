import { defineEventHandler, getQuery } from "h3";
import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../../../utils/api";

export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const query = getQuery(event);
  const forecastId = event.context.params?.forecastId;
  const method = query.method as string;

  if (!forecastId) {
    throw createError({
      statusCode: 400,
      statusMessage: "forecast_id is required",
    });
  }

  if (!method) {
    throw createError({
      statusCode: 400,
      statusMessage: "method parameter is required",
    });
  }

  try {
    const response = await authenticatedFetch<{
      forecast_id: string;
      method: string;
      forecasts: Array<{
        item_id: string;
        method_used: string;
        predictions: Array<{
          date: string;
          point_forecast: number;
          quantiles?: {
            p10?: number;
            p50?: number;
            p90?: number;
          };
        }>;
      }>;
    }>(event, `/api/v1/forecast/${forecastId}/results?method=${encodeURIComponent(method)}`);

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
      statusMessage: getErrorMessage(error) ?? "Failed to fetch forecast results",
    });
  }
});

