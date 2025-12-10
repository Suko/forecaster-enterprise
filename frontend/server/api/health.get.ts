/**
 * Health check endpoint for container orchestration
 * Returns frontend service status
 */
export default defineEventHandler(() => {
  return {
    status: "healthy",
    timestamp: new Date().toISOString(),
    services: {
      frontend: "up",
    },
  };
});
