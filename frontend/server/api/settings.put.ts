import { authenticatedFetch, getErrorMessage, getErrorStatusCode } from "../utils/api";
import type { ClientSettings, ClientSettingsUpdate } from "~/composables/useSettings";

/**
 * Update client settings
 * PUT /api/settings
 */
export default defineEventHandler(async (event) => {
  await requireUserSession(event);

  const body = await readBody<ClientSettingsUpdate>(event);

  try {
    return await authenticatedFetch<ClientSettings>(event, "/api/v1/settings", {
      method: "PUT",
      body: JSON.stringify(body),
    });
  } catch (error: unknown) {
    if (getErrorStatusCode(error) === 401) {
      throw createError({ statusCode: 401, statusMessage: "Not authenticated" });
    }
    throw createError({
      statusCode: getErrorStatusCode(error) || 500,
      statusMessage: getErrorMessage(error) || "Failed to update settings",
    });
  }
});
