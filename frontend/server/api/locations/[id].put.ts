import { authenticatedFetch } from "../../utils/api";
import type { Location } from "~/types/location";

export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const id = event.context.params?.id;
  if (!id) {
    throw createError({ statusCode: 400, statusMessage: "Missing id" });
  }

  const body = await readBody(event);

  try {
    return await authenticatedFetch<Location>(event, `/api/v1/locations/${encodeURIComponent(id)}`, {
      method: "PUT",
      body,
    });
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to update location",
    });
  }
});

