import { authenticatedFetch } from "../../utils/api";

export default defineEventHandler(async (event) => {
  // Require user session (auto-imported by nuxt-auth-utils)
  await requireUserSession(event);
  const id = getRouterParam(event, "id");
  await authenticatedFetch(event, `/api/v1/auth/users/${id}`, {
    method: "DELETE",
  });
  return {};
});
