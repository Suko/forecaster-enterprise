/**
 * Recommendation Types
 * Based on backend API reference
 */

export type RecommendationType = 
  | 'REORDER' 
  | 'URGENT' 
  | 'REDUCE_ORDER' 
  | 'DEAD_STOCK' 
  | 'PROMOTE'

export type RecommendationPriority = 'high' | 'medium' | 'low'

export interface Recommendation {
  type: RecommendationType
  priority: RecommendationPriority
  item_id: string
  product_name: string
  reason: string
  suggested_quantity?: number
  supplier_id?: string
  supplier_name?: string
}

export interface RecommendationFilters {
  recommendation_type?: RecommendationType
  role?: 'CEO' | 'PROCUREMENT' | 'MARKETING'
  priority?: RecommendationPriority
}
