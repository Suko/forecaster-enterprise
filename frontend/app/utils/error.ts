function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function getString(value: unknown): string | undefined {
  if (typeof value === "string" && value.length > 0) return value;
}

export function getErrorText(error: unknown, fallback: string): string {
  if (error instanceof Error) {
    return error.message || fallback;
  }

  if (isRecord(error)) {
    const data = error.data;
    if (isRecord(data)) {
      const detail =
        getString(data.detail) || getString(data.statusMessage) || getString(data.message);
      if (detail) return detail;
    }

    const statusMessage = getString(error.statusMessage);
    if (statusMessage) return statusMessage;

    const message = getString(error.message);
    if (message) return message;
  }

  if (typeof error === "string" && error.length > 0) {
    return error;
  }

  return fallback;
}

