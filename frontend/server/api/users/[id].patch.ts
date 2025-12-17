import { z } from "zod";
import { authenticatedFetch } from "../../utils/api";

const bodySchema = z.object({
  name: z.string().optional(),
  role: z.enum(["admin", "user"]).optional(),
  is_active: z.boolean().optional(),
});

export default defineEventHandler(async (event) => {
  try {
    // Require user session (auto-imported by nuxt-auth-utils)
    await requireUserSession(event);
    const id = getRouterParam(event, "id");
    const body = await readValidatedBody(event, bodySchema.parse);
    return await authenticatedFetch(event, `/auth/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    });
  } catch (error: any) {
    throw error;
  }
});
