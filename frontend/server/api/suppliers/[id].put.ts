import { logger } from "~~/server/utils/logger";
import { authenticatedFetch } from "../../utils/api";
import type { Supplier } from "~/types/supplier";

/**
 * Update supplier information
 * PUT /api/suppliers/:id
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const id = event.context.params?.id;
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: "Missing id" });
  }

  const body = await readBody(event);

  try {
    return await authenticatedFetch<Supplier>(
      event,
      `/api/v1/suppliers/${encodeURIComponent(id)}`,
      {
        method: "PUT",
        body,
      }
    );
  } catch (error: any) {
    logger.error("Update supplier error", { error });
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to update supplier",
    });
  }
});
