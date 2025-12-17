import * as Sentry from "@sentry/nuxt";
import { getMachineId, setMachineId } from "../utils/logger";

const MACHINE_ID_STATUS_FILE = "/license-data/license-status.json";
const LOAD_RETRY_MS = 5000;

let lastLoadAttemptAt = 0;
let inFlightLoad: Promise<void> | null = null;

async function ensureMachineIdLoaded(): Promise<void> {
  if (getMachineId()) return;

  const now = Date.now();
  if (now - lastLoadAttemptAt < LOAD_RETRY_MS) return;

  if (inFlightLoad) {
    await inFlightLoad;
    return;
  }

  lastLoadAttemptAt = now;

  inFlightLoad = (async () => {
    try {
      const { readFile } = await import("node:fs/promises");
      const content = await readFile(MACHINE_ID_STATUS_FILE, "utf-8");
      const parsed = JSON.parse(content) as { machineId?: unknown };
      if (typeof parsed.machineId === "string" && parsed.machineId) {
        setMachineId(parsed.machineId);
      }
    } catch {
      // ignore: file may not exist in local dev or during startup
    } finally {
      inFlightLoad = null;
    }
  })();

  await inFlightLoad;
}

export default defineEventHandler(async (event) => {
  await ensureMachineIdLoaded();
  const machineId = getMachineId();
  if (machineId) {
    Sentry.setTag("machine_id", machineId);
  }
});
