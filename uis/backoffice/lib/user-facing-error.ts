const SAFE_API_DETAILS = new Set([
  "Invalid credentials",
  "Inactive user",
  "User not found",
  "Profile not found",
  "Invalid or expired token",
  "Current password is incorrect",
  "Email already exists",
  "Forbidden",
  "Could not validate credentials",
  "Authentication required",
  "No file uploaded.",
  "File is empty.",
  "Incorrect format: upload a .csv file.",
  "Incorrect format: file must be UTF-8 encoded CSV.",
  "Supplier not found.",
  "No analysis results available. Upload a CSV first.",
  "Could not read the uploaded file.",
  "Service temporarily unavailable. Please try again.",
  "Internal server error",
  "Invalid request. Please check the submitted data.",
  "Candidate not found.",
  "Note not found.",
  "Note content is required.",
  "Request body must be valid JSON.",
  "Full name is required.",
  "Email is required.",
  "Position is required.",
  "Application date is required.",
  "A valid status is required.",
  "A valid stage is required.",
]);

export function messageForHttpStatus(status: number): string {
  if (status === 400) {
    return "The request could not be processed. Please check your input and try again.";
  }
  if (status === 401) {
    return "Your session expired. Please sign in again.";
  }
  if (status === 403) {
    return "You do not have permission to do that.";
  }
  if (status === 404) {
    return "The requested record was not found.";
  }
  if (status === 409) {
    return "That email is already registered.";
  }
  if (status === 422) {
    return "Please check the form fields and try again.";
  }
  if (status === 503) {
    return "The service is temporarily unavailable. Please try again.";
  }
  return "Something went wrong. Please try again.";
}

export function sanitizeApiDetail(status: number, detail: string | undefined): string {
  if (detail && SAFE_API_DETAILS.has(detail)) {
    return detail;
  }
  return messageForHttpStatus(status);
}

export function getUserFacingError(error: unknown, fallback: string): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    typeof (error as { status: unknown }).status === "number" &&
    "message" in error &&
    typeof (error as { message: unknown }).message === "string"
  ) {
    return sanitizeApiDetail(
      (error as { status: number }).status,
      (error as { message: string }).message,
    );
  }

  if (error instanceof Error) {
    const message = error.message;
    if (
      SAFE_API_DETAILS.has(message) &&
      !/Request failed|Unexpected token|Failed to fetch|status \d+/i.test(message)
    ) {
      return message;
    }
    if (/Failed to fetch/i.test(message)) {
      return "Unable to reach the service. Please try again.";
    }
  }

  return fallback;
}

export async function readResponseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch {
    throw new Error("Something went wrong. Please try again.");
  }
}
