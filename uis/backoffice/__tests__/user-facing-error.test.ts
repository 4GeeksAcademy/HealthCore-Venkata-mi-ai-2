import {
  getUserFacingError,
  messageForHttpStatus,
  sanitizeApiDetail,
} from "@/lib/user-facing-error";

describe("sanitizeApiDetail", () => {
  test("passes through known staff-facing API details", () => {
    expect(sanitizeApiDetail(401, "Invalid credentials")).toBe("Invalid credentials");
    expect(sanitizeApiDetail(400, "Current password is incorrect")).toBe(
      "Current password is incorrect",
    );
  });

  test("replaces unknown details with safe status copy", () => {
    expect(sanitizeApiDetail(500, "Traceback (most recent call last)")).toBe(
      "Something went wrong. Please try again.",
    );
    expect(sanitizeApiDetail(401, "JWTError: Signature verification failed")).toBe(
      "Your session expired. Please sign in again.",
    );
  });
});

describe("getUserFacingError", () => {
  test("uses a known API message on a structured error", () => {
    expect(
      getUserFacingError({ status: 409, message: "Email already exists" }, "fallback"),
    ).toBe("Email already exists");
  });

  test("maps network failures and unknown errors to safe copy", () => {
    expect(getUserFacingError(new Error("Failed to fetch"), "fallback")).toBe(
      "Unable to reach the service. Please try again.",
    );
    expect(getUserFacingError(new Error("Unexpected token < in JSON"), "Try again later.")).toBe(
      "Try again later.",
    );
  });
});

describe("messageForHttpStatus", () => {
  test("returns the session-expired copy for 401", () => {
    expect(messageForHttpStatus(401)).toBe("Your session expired. Please sign in again.");
  });

  test("returns generic retry copy for an unknown status", () => {
    expect(messageForHttpStatus(418)).toBe("Something went wrong. Please try again.");
  });
});
