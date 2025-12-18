import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../utils/api";
import type { DashboardResponse } from "~/types/dashboard";

/**
 * Fetch dashboard data from backend
 * GET /api/dashboard
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  try {
    const dashboardData = await authenticatedFetch<DashboardResponse>(event, "/api/v1/dashboard");

    return dashboardData;
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) ?? 500,
      statusMessage: getErrorMessage(error) ?? "Failed to fetch dashboard data",
    });
  }
});
