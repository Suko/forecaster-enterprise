/**
 * Composable for Chart.js integration
 * Handles chart data fetching and configuration
 */

import type { TimePeriod, TrendDataPoint } from "~/types/dashboard";
import { logger } from "~~/server/utils/logger";

export const useDashboardCharts = () => {
  const { apiCall } = useApi();
  const config = useRuntimeConfig();

  /**
   * Fetch trend data for dashboard charts
   */
  const fetchTrendData = async (period: TimePeriod = "monthly"): Promise<TrendDataPoint[]> => {
    try {
      // TODO: Update when backend endpoint is available
      // For now, return empty array
      // const response = await apiCall<TrendDataPoint[]>(
      //   `/dashboard/trends?period=${period}`
      // )
      // return response

      return [];
    } catch (error) {
      logger.error("Error fetching trend data", { error });
      return [];
    }
  };

  /**
   * Format data for Chart.js
   */
  const formatChartData = (data: TrendDataPoint[], label: string) => {
    return {
      labels: data.map((d) => d.date),
      datasets: [
        {
          label,
          data: data.map((d) => d.value),
          borderColor: "rgb(59, 130, 246)",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          tension: 0.4,
        },
      ],
    };
  };

  return {
    fetchTrendData,
    formatChartData,
  };
};
