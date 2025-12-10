import { authenticatedFetch } from '../utils/api'
import type { Recommendation } from '~/types/recommendation'

/**
 * Fetch recommendations from backend
 * GET /api/recommendations
 */
export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event)

  try {
    const query = getQuery(event)
    const queryString = new URLSearchParams(
      Object.entries(query).filter(([_, v]) => v !== undefined && v !== null && v !== '')
        .map(([k, v]) => [k, String(v)])
    ).toString()

    const recommendations = await authenticatedFetch<Recommendation[]>(
      event,
      `/api/v1/order-planning/recommendations${queryString ? `?${queryString}` : ''}`
    )

    return recommendations
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({
        statusCode: 401,
        statusMessage: 'Not authenticated',
      })
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || 'Failed to fetch recommendations',
    })
  }
})
