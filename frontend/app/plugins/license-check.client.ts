/**
 * License Check Plugin
 *
 * Checks license status via the frontend API (which reads from shared volume).
 * When license is invalid, redirects to the license error page.
 * When license becomes valid again, redirects back to home.
 *
 * Optimized to:
 * - Only check when tab is visible
 * - Check on route navigation
 * - Use reasonable intervals (60s)
 * - Retry initial check to handle slow startup
 *
 * Note: This is a .client.ts file, so it only runs on the client side.
 * Type errors for Nuxt auto-imports resolve after `nuxt prepare` generates types.
 */

import { logger } from "~~/server/utils/logger";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type RouteLocation = { path: string; [key: string]: any };

interface LicenseStatus {
  valid: boolean;
  reason?: string;
  checkedAt: string;
}

export default defineNuxtPlugin((nuxtApp) => {
  const router = useRouter();

  let intervalId: ReturnType<typeof setInterval> | null = null;
  let lastCheckTime = 0;
  let initialCheckDone = false;
  const CHECK_INTERVAL = 60000; // 60 seconds
  const MIN_CHECK_GAP = 10000; // Don't check more than once per 10 seconds
  const INITIAL_RETRIES = 3; // Retry initial check up to 3 times
  const RETRY_DELAY = 2000; // Wait 2s between retries

  // Check license status via frontend API (reads from shared volume)
  const checkLicenseStatus = async (): Promise<LicenseStatus | null> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch("/api/license-status", {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) return null;

      return (await response.json()) as LicenseStatus;
    } catch (error) {
      logger.error("Error checking license status", { error });
      return null;
    }
  };

  // Handle license check result (only redirect if initial check is done)
  const handleLicenseCheck = async (): Promise<void> => {
    const now = Date.now();

    // Throttle checks
    if (now - lastCheckTime < MIN_CHECK_GAP) return;
    lastCheckTime = now;

    const currentPath = window.location.pathname;
    const status = await checkLicenseStatus();

    // Only redirect if we've done initial check (avoid false positives on startup)
    if (!initialCheckDone) return;

    // If we couldn't get status, don't redirect (fail open)
    if (!status) return;

    if (!status.valid && currentPath !== "/license-error") {
      // License invalid - redirect to license error
      window.location.href = "/license-error";
    } else if (status.valid && currentPath === "/license-error") {
      // License valid again - redirect to home
      window.location.href = "/";
    }
  };

  // Initial check with retries (handles slow startup)
  const doInitialCheck = async (): Promise<void> => {
    // Skip if already on license error page
    if (window.location.pathname === "/license-error") {
      initialCheckDone = true;
      return;
    }

    for (let i = 0; i < INITIAL_RETRIES; i++) {
      const status = await checkLicenseStatus();
      if (status?.valid) {
        initialCheckDone = true;
        return;
      }
      // If status is explicitly invalid (not just null/error), redirect immediately
      if (status && !status.valid) {
        initialCheckDone = true;
        window.location.href = "/license-error";
        return;
      }
      // Wait before retry (unless last attempt)
      if (i < INITIAL_RETRIES - 1) {
        await new Promise((resolve) => setTimeout(resolve, RETRY_DELAY));
      }
    }

    // All retries returned null (couldn't reach API) - assume OK, don't block user
    initialCheckDone = true;
  };

  // Start periodic checking (only when visible)
  const startChecking = (): void => {
    if (intervalId) return;
    intervalId = setInterval(() => void handleLicenseCheck(), CHECK_INTERVAL);
  };

  // Stop periodic checking
  const stopChecking = (): void => {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  };

  // Handle visibility change - pause when hidden, resume when visible
  const handleVisibilityChange = (): void => {
    if (document.hidden) {
      stopChecking();
    } else {
      // Check immediately when becoming visible, then start interval
      void handleLicenseCheck();
      startChecking();
    }
  };

  // Initial check using app:mounted hook
  nuxtApp.hook("app:mounted", () => {
    // Small delay to let license-watcher write initial status
    setTimeout(() => {
      void doInitialCheck().then(() => {
        // Only start interval if tab is visible and initial check done
        if (!document.hidden) {
          startChecking();
        }
      });
    }, 1000);
  });

  // Listen for visibility changes
  document.addEventListener("visibilitychange", handleVisibilityChange);

  // Check on route navigation (catches issues faster than interval)
  router.beforeEach(async (to: RouteLocation, from: RouteLocation) => {
    // Don't check if navigating to/from license error page
    if (to.path === "/license-error" || from.path === "/license-error") return;

    // Skip navigation check until initial check is done
    if (!initialCheckDone) return;

    // Quick license check on navigation
    const status = await checkLicenseStatus();
    if (status && !status.valid) {
      return "/license-error";
    }
  });
});
