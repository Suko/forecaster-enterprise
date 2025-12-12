import { authenticatedFetch } from "../utils/api";

export default defineEventHandler(async (event) => {
  // Require user session (auto-imported by nuxt-auth-utils)
  await requireUserSession(event);
  return await authenticatedFetch(event, "/auth/users");
});

