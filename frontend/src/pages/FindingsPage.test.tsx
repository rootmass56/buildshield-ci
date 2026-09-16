import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("../state/ScanContext", () => ({
  useScanState: () => ({
    latestScan: {
      run_id: "scan-xss",
      kind: "scan",
      target_path: "samples/vulnerable-repo",
      summary: {
        target_path: "samples/vulnerable-repo",
        files_discovered: 1,
        files_scanned: 1,
        findings_count: 1,
        critical_count: 0,
        high_count: 1,
        medium_count: 0,
        low_count: 0,
        info_count: 0,
        security_score: 80,
        risk_level: "HIGH",
      },
      risk_profile: {
        overall_security_score: 80,
        overall_risk_level: "HIGH",
        build_gate_status: "FAILED",
        build_gate_reason: "Security gate failed.",
        category_risks: [],
        top_risk_drivers: [],
      },
      policy_evaluation: {
        policy_file: "buildshield-policy.yml",
        passed: false,
        minimum_score: 80,
        actual_score: 80,
        fail_on_severities: ["HIGH"],
        violations: [],
      },
      findings: [
        {
          rule_id: "DG-XSS-TEST",
          title: '<img src=x onerror=alert("xss")>',
          severity: "HIGH",
          category: "TEST",
          confidence: "HIGH",
          description: "Repository-controlled test content.",
          impact: "XSS regression test.",
          evidence: {
            file_path: "package.json",
            line_number: 1,
            snippet: "<script>window.__buildshield_xss = true</script>",
          },
          remediation: "Render as text.",
          reference: null,
        },
      ],
      reports: [],
      history_record: {
        id: 1,
        run_id: "scan-xss",
        created_at: "2026-09-15T00:00:00Z",
        kind: "scan",
        target_path: "samples/vulnerable-repo",
        security_score: 80,
        risk_level: "HIGH",
        findings_count: 1,
        critical_count: 0,
        high_count: 1,
        medium_count: 0,
        low_count: 0,
        info_count: 0,
        policy_status: "FAILED",
        build_gate_status: "FAILED",
        report_count: 0,
      },
    },
    setLatestScan: vi.fn(),
  }),
}));

import { FindingsPage } from "./FindingsPage";

describe("FindingsPage XSS rendering", () => {
  it("renders repository-controlled HTML-looking content as inert text", () => {
    const maliciousTitle = '<img src=x onerror=alert("xss")>';
    const maliciousSnippet =
      "<script>window.__buildshield_xss = true</script>";

    const { container } = render(
      <MemoryRouter>
        <FindingsPage />
      </MemoryRouter>,
    );

    expect(
      screen.getByText((content) => content.includes(maliciousTitle)),
    ).toBeInTheDocument();

    expect(screen.getByText(maliciousSnippet)).toBeInTheDocument();
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector("[onerror]")).toBeNull();
    expect(container.querySelector("img")).toBeNull();
  });
});
