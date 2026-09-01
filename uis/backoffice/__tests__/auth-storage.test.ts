import { clearAuthToken, getAuthToken, setAuthToken } from "@/lib/auth-storage";

const AUTH_TOKEN_KEY = "healthcore.backoffice.access_token";

describe("auth token storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  test("round-trips a session token", () => {
    setAuthToken("staff-session-token");
    expect(getAuthToken()).toBe("staff-session-token");
    expect(window.localStorage.getItem(AUTH_TOKEN_KEY)).toBe("staff-session-token");
  });

  test("clearing storage returns no token", () => {
    setAuthToken("staff-session-token");
    clearAuthToken();
    expect(getAuthToken()).toBeNull();
  });
});
