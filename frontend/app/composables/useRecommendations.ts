/**
 * Composable for Recommendations
 * Handles fetching and managing recommendations
 */

import type { Recommendation, RecommendationFilters } from "~/types/recommendation";

export const useRecommendations = () => {
  /**
   * Fetch recommendations with filters
   */
  const fetchRecommendations = async (
    filters?: RecommendationFilters
  ): Promise<Recommendation[]> => {
    try {
      const queryParams = new URLSearchParams();
      
      if (filters?.recommendation_type) {
        queryParams.append("type", filters.recommendation_type);
      }
      if (filters?.role) {
        queryParams.append("role", filters.role);
      }

      const queryString = queryParams.toString();
      const response = await $fetch<Recommendation[]>(
        `/api/recommendations${queryString ? `?${queryString}` : ""}`
      );

      return response;
    } catch (error: any) {
      // Re-throw 401 errors so they can be handled by the page
      // Other errors are also re-thrown
      console.error("Error fetching recommendations:", error);
      throw error;
    }
  };

  /**
   * Add recommendation to cart
   */
  const addToCart = async (itemId: string, supplierId?: string, quantity?: number) => {
    try {
      await $fetch("/api/order-planning/cart/add", {
        method: "POST",
        body: {
          item_id: itemId,
          supplier_id: supplierId,
          quantity: quantity,
        },
      });
    } catch (error: any) {
      // Re-throw 401 errors so they can be handled by the page
      // Other errors are also re-thrown
      console.error("Error adding to cart:", error);
      throw error;
    }
  };

  return {
    fetchRecommendations,
    addToCart,
  };
};
