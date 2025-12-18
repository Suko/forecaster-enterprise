import { readFile, stat } from "fs/promises";
import { existsSync } from "fs";
import { setMachineId } from "../utils/logger";

interface LicenseStatus {
  valid: boolean;
  reason?: string;
  checkedAt: string;
  machineId?: string;
}

// Grace period from license-watcher (default 48 hours)
// If status file is older than this, license-watcher has likely stopped
const GRACE_PERIOD_SECONDS = parseInt(process.env.LICENSE_GRACE_PERIOD || "172800", 10);
const MAX_STATUS_AGE_MS = GRACE_PERIOD_SECONDS * 1000;

/**
 * GET /api/license-status
 *
 * Returns the current license status from the shared volume.
 * This file is written by the license-watcher container.
 *
 * Security: If file doesn't exist or is stale, assume invalid.
 * This prevents bypassing license check by disabling license-watcher.
 *
 * Development mode: Bypass license check when running locally (not in Docker).
 */
export default defineEventHandler(async (): Promise<LicenseStatus> => {
  // Bypass license check in development/local mode
  const isDevelopment =
    process.env.NODE_ENV === "development" ||
    process.env.ENVIRONMENT === "development" ||
    process.env.ENVIRONMENT === "dev" ||
    process.env.ENVIRONMENT === "local";

  // If running locally (not in Docker), the license file won't exist
  // Check if we're in Docker by checking if the path exists or if we're in dev mode
  const statusFilePath = "/license-data/license-status.json";

  // In development, if file doesn't exist, assume valid (local development)
  if (isDevelopment && !existsSync(statusFilePath)) {
    return {
      valid: true,
      checkedAt: new Date().toISOString(),
    };
  }

  // Check if file exists
  if (!existsSync(statusFilePath)) {
    // No status file - license-watcher may not be running
    return {
      valid: false,
      reason: "license_check_unavailable",
      checkedAt: new Date().toISOString(),
    };
  }

  try {
    // Check file age - if too old, license-watcher may have stopped
    const fileStat = await stat(statusFilePath);
    const fileAge = Date.now() - fileStat.mtime.getTime();

    if (fileAge > MAX_STATUS_AGE_MS) {
      return {
        valid: false,
        reason: "license_check_stale",
        checkedAt: fileStat.mtime.toISOString(),
      };
    }

    const content = await readFile(statusFilePath, "utf-8");
    const status = JSON.parse(content) as LicenseStatus;

    // Cache machine ID for logger
    if (status.machineId) {
      setMachineId(status.machineId);
    }

    return status;
  } catch {
    return {
      valid: false,
      reason: "license_check_error",
      checkedAt: new Date().toISOString(),
    };
  }
});
