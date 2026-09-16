import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import { AuthProvider } from "./auth/AuthContext";
import { ScanProvider } from "./state/ScanContext";

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json",
    },
  });
}

function requestPath(input: RequestInfo | URL): string {
  if (typeof input === "string") {
    return input;
  }

  if (input instanceof URL) {
    return `${input.pathname}${input.search}`;
  }

  const url = new URL(input.url, "http://localhost");
  return `${url.pathname}${url.search}`;
}

function renderApp(initialPath = "/") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <ScanProvider>
          <App />
        </ScanProvider>
      </AuthProvider>
    </MemoryRouter>,
  );
}

function metricCard(label: string): HTMLElement {
  const labelElement = screen.getByText(label);
  const card = labelElement.closest("article");

  if (card === null) {
    throw new Error(`Metric card not found for label: ${label}`);
  }

  return card;
}

describe("BuildShield-CI React application", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  it("redirects unauthenticated users to login", async () => {
    vi.mocked(fetch).mockImplementation(async (input) => {
      const path = requestPath(input);

      if (path === "/api/auth/session") {
        return jsonResponse({ authenticated: false });
      }

      return jsonResponse({ detail: `Unexpected request: ${path}` }, 500);
    });

    renderApp("/");

    expect(
      await screen.findByRole("heading", { name: "Sign in to BuildShield-CI" }),
    ).toBeInTheDocument();
  });

  it("renders protected overview data", async () => {
    vi.mocked(fetch).mockImplementation(async (input) => {
      const path = requestPath(input);

      if (path === "/api/auth/session") {
        return jsonResponse({
          authenticated: true,
          username: "admin",
          csrf_token: "csrf-test-token",
          expires_at: 9999999999,
        });
      }

      if (path === "/api/history?limit=5") {
        return jsonResponse({
          history: [
            {
              id: 1,
              run_id: "scan-1",
              created_at: "2026-09-15T00:00:00Z",
              kind: "scan",
              target_path: "samples/secure-repo",
              security_score: 100,
              risk_level: "LOW",
              findings_count: 0,
              critical_count: 0,
              high_count: 0,
              medium_count: 0,
              low_count: 0,
              info_count: 0,
              policy_status: "PASSED",
              build_gate_status: "WARNING",
              report_count: 1,
            },
          ],
        });
      }

      if (path === "/api/reports") {
        return jsonResponse({ reports: [] });
      }

      return jsonResponse({ detail: `Unexpected request: ${path}` }, 500);
    });

    renderApp("/app");

    expect(
      await screen.findByRole("heading", {
        name: "Security posture overview",
      }),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(
        within(metricCard("Latest score")).getByText("100/100"),
      ).toBeInTheDocument();
    });

    expect(screen.getByText("admin")).toBeInTheDocument();
  });

  it("sends CSRF on protected scan", async () => {
    vi.mocked(fetch).mockImplementation(async (input, init) => {
      const path = requestPath(input);

      if (path === "/api/auth/session") {
        return jsonResponse({
          authenticated: true,
          username: "admin",
          csrf_token: "csrf-test-token",
          expires_at: 9999999999,
        });
      }

      if (path === "/api/sample-repositories") {
        return jsonResponse({
          repositories: [
            {
              label: "Realistic Application Repository",
              path: "samples/realistic-repo",
              description: "Mixed posture",
            },
            {
              label: "Hardened Benchmark Repository",
              path: "samples/secure-repo",
              description: "Benchmark",
            },
          ],
          default_policy: "buildshield-policy.yml",
        });
      }

      if (path === "/api/scan") {
        const headers = new Headers(init?.headers);

        expect(headers.get("X-CSRF-Token")).toBe("csrf-test-token");
        expect(JSON.parse(String(init?.body)).target_path).toBe(
          "samples/realistic-repo",
        );

        return jsonResponse({
          run_id: "scan-1",
          kind: "scan",
          target_path: "samples/realistic-repo",
          summary: {
            target_path: "samples/realistic-repo",
            files_discovered: 7,
            files_scanned: 7,
            findings_count: 3,
            critical_count: 0,
            high_count: 0,
            medium_count: 2,
            low_count: 1,
            info_count: 0,
            security_score: 81,
            risk_level: "MEDIUM",
          },
          risk_profile: {
            overall_security_score: 81,
            overall_risk_level: "MEDIUM",
            build_gate_status: "WARNING",
            build_gate_reason: "Security score is acceptable but improvements are recommended.",
            category_risks: [],
            top_risk_drivers: [],
          },
          policy_evaluation: {
            policy_file: "buildshield-policy.yml",
            passed: true,
            minimum_score: 80,
            actual_score: 81,
            fail_on_severities: ["CRITICAL"],
            violations: [],
          },
          findings: [],
          reports: [],
          history_record: {
            id: 1,
            run_id: "scan-1",
            created_at: "2026-09-15T00:00:00Z",
            kind: "scan",
            target_path: "samples/realistic-repo",
            security_score: 81,
            risk_level: "MEDIUM",
            findings_count: 3,
            critical_count: 0,
            high_count: 0,
            medium_count: 2,
            low_count: 1,
            info_count: 0,
            policy_status: "PASSED",
            build_gate_status: "WARNING",
            report_count: 0,
          },
        });
      }

      return jsonResponse({ detail: `Unexpected request: ${path}` }, 500);
    });

    renderApp("/app/scanner");

    const button = await screen.findByRole("button", {
      name: "Run security scan",
    });

    fireEvent.click(button);

    await waitFor(() => {
      expect(
        within(metricCard("Security score")).getByText("81/100"),
      ).toBeInTheDocument();
    });

    const scanCalls = vi
      .mocked(fetch)
      .mock.calls.filter(([input]) => requestPath(input) === "/api/scan");

    expect(scanCalls).toHaveLength(1);
  });
});
