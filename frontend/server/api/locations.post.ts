import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../utils/api";
import type { Location } from "~/types/location";

export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const body = await readBody(event);

  try {
    return await authenticatedFetch<Location>(event, "/api/v1/locations", {
      method: "POST",
      body,
    });
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to create location",
    });
  }
});
