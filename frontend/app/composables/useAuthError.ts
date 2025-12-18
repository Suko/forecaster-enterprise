/**
 * Composable for handling authentication errors
 * Automatically redirects to login on 401 errors
 */
export const useAuthError = () => {
  const { clear } = useUserSession();
  const route = useRoute();

  const getStatusCode = (error: unknown): number | undefined => {
    if (typeof error !== "object" || error === null) return;
    if ("statusCode" in error && typeof (error as { statusCode?: unknown }).statusCode === "number") {
      return (error as { statusCode: number }).statusCode;
    }
    if ("status" in error && typeof (error as { status?: unknown }).status === "number") {
      return (error as { status: number }).status;
    }
    if ("response" in error) {
      const response = (error as { response?: unknown }).response;
      if (typeof response === "object" && response !== null) {
        const status = (response as { status?: unknown }).status;
        if (typeof status === "number") return status;
      }
    }
  };

  /**
   * Handle API errors and redirect to login if 401
   * @returns true if error was a 401 and was handled, false otherwise
   */
  const handleAuthError = async (error: unknown): Promise<boolean> => {
    // Check if it's a 401 Unauthorized error
    if (getStatusCode(error) === 401) {
      // Clear session
      await clear();

      // Redirect to login with return URL
      const returnTo = route.fullPath !== "/login" ? route.fullPath : undefined;
      await navigateTo({
        path: "/login",
        query: returnTo ? { returnTo } : undefined,
      });

      return true; // Indicates error was handled
    }
    return false; // Error was not a 401
  };

  return {
    handleAuthError,
  };
};
