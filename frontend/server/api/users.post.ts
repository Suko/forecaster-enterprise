import { z } from "zod";
import { authenticatedFetch } from "../utils/api";

const bodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(128),
  name: z.string().optional(),
});

export default defineEventHandler(async (event) => {
  // Require user session (auto-imported by nuxt-auth-utils)
  await requireUserSession(event);
  const body = await readValidatedBody(event, bodySchema.parse);
  return await authenticatedFetch(event, "/auth/users", {
    method: "POST",
    body: JSON.stringify(body),
  });
});

