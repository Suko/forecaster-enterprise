import { readFile, stat } from "fs/promises";
import { existsSync } from "fs";

interface LicenseStatus {
  valid: boolean;
  reason?: string;
  checkedAt: string;
}

// Grace period from license-watcher (default 48 hours)
// If status file is older than this, license-watcher has likely stopped
const GRACE_PERIOD_SECONDS = parseInt(
  process.env.LICENSE_GRACE_PERIOD || "172800",
  10
);
const MAX_STATUS_AGE_MS = GRACE_PERIOD_SECONDS * 1000;

/**
 * GET /api/license-status
 *
 * Returns the current license status from the shared volume.
 * This file is written by the license-watcher container.
 *
 * Security: If file doesn't exist or is stale, assume invalid.
 * This prevents bypassing license check by disabling license-watcher.
 */
export default defineEventHandler(async (): Promise<LicenseStatus> => {
  const statusFilePath = "/license-data/license-status.json";

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
    return status;
  } catch {
    // Error reading file - assume invalid to be safe
    return {
      valid: false,
      reason: "license_check_error",
      checkedAt: new Date().toISOString(),
    };
  }
});
