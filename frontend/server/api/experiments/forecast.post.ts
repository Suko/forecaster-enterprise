import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";
import type { ForecastResponse, TestBedForecastRequest } from "~/types/experiments";

/**
 * Generate forecast for test bed
 * POST /api/experiments/forecast
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const body = await readBody<TestBedForecastRequest>(event);

  if (!body.item_ids || body.item_ids.length === 0) {
    throw createError({
      statusCode: 400,
      statusMessage: "item_ids is required",
    });
  }

  try {
    const response = await authenticatedFetch<ForecastResponse>(event, "/api/v1/forecast", {
      method: "POST",
      body: JSON.stringify({
        item_ids: body.item_ids,
        prediction_length: body.prediction_length || 30,
        model: body.model || "chronos-2",
        include_baseline: body.include_baseline ?? true,
        run_all_methods: body.run_all_methods ?? true, // Test Bed: run all methods for comparison
        skip_persistence: body.skip_persistence ?? true, // Test Bed: don't save to database
        training_end_date: body.training_end_date || null,
      }),
    });

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
      statusMessage: getErrorMessage(error) ?? "Failed to generate forecast",
    });
  }
});

