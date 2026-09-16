import { describe, expect, it } from "vitest";

import { safeOsvUrl } from "./security";

describe("safeOsvUrl", () => {
  it("accepts HTTPS links on osv.dev", () => {
    expect(
      safeOsvUrl("https://osv.dev/vulnerability/GHSA-test"),
    ).toBe("https://osv.dev/vulnerability/GHSA-test");
  });

  it("rejects non-HTTPS, lookalike and script URLs", () => {
    expect(
      safeOsvUrl("http://osv.dev/vulnerability/GHSA-test"),
    ).toBeNull();

    expect(
      safeOsvUrl("https://osv.dev.evil.example/vulnerability/GHSA-test"),
    ).toBeNull();

    expect(
      safeOsvUrl("javascript:alert(1)"),
    ).toBeNull();
  });
});
