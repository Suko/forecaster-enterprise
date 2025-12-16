import { authenticatedFetch } from "../utils/api";
import type { DashboardResponse } from "~/types/dashboard";
import { logger } from "../utils/logger";

/**
 * Fetch dashboard data from backend
 * GET /api/dashboard
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event);

  try {
    const dashboardData = await authenticatedFetch<DashboardResponse>(event, "/api/v1/dashboard");

    return dashboardData;
  } catch (error: any) {
    logger.error("Dashboard fetch error", { error });
    if (error.statusCode === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: "Not authenticated",
      });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to fetch dashboard data",
    });
  }
});
