import { resolveApiUrl } from "@/lib/authed-fetch";

describe("resolveApiUrl", () => {
  test("does not double a relative /hc-api prefix used in Compose", () => {
    expect(resolveApiUrl("/hc-api/suppliers", "/hc-api")).toBe("/hc-api/suppliers");
    expect(resolveApiUrl("/suppliers", "/hc-api")).toBe("/hc-api/suppliers");
  });

  test("keeps absolute FastAPI origins", () => {
    expect(resolveApiUrl("http://localhost:8001/suppliers", "/hc-api")).toBe(
      "http://localhost:8001/suppliers",
    );
    expect(resolveApiUrl("/inventory/products", "http://localhost:8001")).toBe(
      "http://localhost:8001/inventory/products",
    );
  });
});
