import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../../utils/api";
import type { BackfillActualsRequest, BackfillActualsResponse } from "~/types/experiments";

/**
 * Backfill actual values for quality testing
 * POST /api/experiments/actuals
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const body = await readBody<BackfillActualsRequest>(event);

  if (!body.item_id) {
    throw createError({
      statusCode: 400,
      statusMessage: "item_id is required",
    });
  }

  if (!body.actuals || body.actuals.length === 0) {
    throw createError({
      statusCode: 400,
      statusMessage: "actuals is required",
    });
  }

  try {
    const response = await authenticatedFetch<BackfillActualsResponse>(event, "/api/v1/forecasts/actuals", {
      method: "POST",
      body: JSON.stringify(body),
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
      statusMessage: getErrorMessage(error) ?? "Failed to backfill actuals",
    });
  }
});

