import * as Sentry from "@sentry/node";
import { getMachineId } from "../utils/logger";

export default defineEventHandler((event) => {
  const machineId = getMachineId();
  if (machineId) {
    Sentry.setTag("machine_id", machineId);
  }
});
