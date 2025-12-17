import { authenticatedFetch } from "../utils/api";

export default defineEventHandler(async (event) => {
  try {
    // Require user session (auto-imported by nuxt-auth-utils)
    await requireUserSession(event);
    return await authenticatedFetch(event, "/auth/users");
  } catch (error: any) {
    // Re-throw so Sentry auto-captures
    throw error;
  }
});
