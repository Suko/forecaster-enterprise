import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";
import type { ForecastModel } from "~/types/experiments";

/**
 * Get available forecast models
 * GET /api/experiments/models
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    const models = await authenticatedFetch<ForecastModel[]>(event, "/api/v1/forecast/models");
    return models;
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) ?? 500,
      statusMessage: getErrorMessage(error) ?? "Failed to fetch models",
    });
  }
});

