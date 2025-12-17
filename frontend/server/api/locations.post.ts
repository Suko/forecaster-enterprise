import { authenticatedFetch } from "../utils/api";
import type { Location } from "~/types/location";

export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const body = await readBody(event);

  try {
    return await authenticatedFetch<Location>(event, `/api/v1/locations`, {
      method: "POST",
      body,
    });
  } catch (error: any) {
    if (error.statusCode === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: error.statusCode || 500,
      statusMessage: error.message || "Failed to create location",
    });
  }
});
