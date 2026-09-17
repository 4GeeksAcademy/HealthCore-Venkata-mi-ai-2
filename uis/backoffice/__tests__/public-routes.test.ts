import { isBackofficePublicPath } from "@/lib/public-routes";

describe("backoffice public routes", () => {
  test("treats auth pages as public", () => {
    expect(isBackofficePublicPath("/login")).toBe(true);
    expect(isBackofficePublicPath("/register")).toBe(true);
    expect(isBackofficePublicPath("/forgot-password")).toBe(true);
    expect(isBackofficePublicPath("/reset-password")).toBe(true);
  });

  test("treats inventory as protected", () => {
    expect(isBackofficePublicPath("/inventory")).toBe(false);
    expect(isBackofficePublicPath(null)).toBe(false);
  });
});
