import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const apiMocks = vi.hoisted(() => ({
  getSampleRepositories: vi.fn(),
  runComparison: vi.fn(),
}));

vi.mock("../api/client", () => ({
  ApiError: class ApiError extends Error {
    readonly status: number;

    constructor(message: string, status: number) {
      super(message);
      this.name = "ApiError";
      this.status = status;
    }
  },
  getSampleRepositories: apiMocks.getSampleRepositories,
  runComparison: apiMocks.runComparison,
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    csrfToken: "csrf-test-token",
  }),
}));

import { ComparePage } from "./ComparePage";

describe("ComparePage workspace paths", () => {
  beforeEach(() => {
    apiMocks.getSampleRepositories.mockResolvedValue({
      repositories: [
        {
          label: "Vulnerable Benchmark Repository",
          path: "samples/vulnerable-repo",
          description: "Controlled vulnerable benchmark.",
        },
        {
          label: "Hardened Benchmark Repository",
          path: "samples/secure-repo",
          description: "Controlled hardened benchmark.",
        },
      ],
      default_policy: "buildshield-policy.yml",
    });

    apiMocks.runComparison.mockResolvedValue({
      run_id: "compare-test",
      kind: "comparison",
      comparison: {
        baseline_label: "repo-a-fastapi-template",
        target_label: "repo-b-vulnreach",
        baseline: {
          summary: {
            security_score: 15,
            findings_count: 56,
            risk_level: "CRITICAL",
          },
        },
        target: {
          summary: {
            security_score: 26,
            findings_count: 49,
            risk_level: "CRITICAL",
          },
        },
        score_delta: 11,
        findings_reduced: 7,
        risk_reduction_percentage: 12.94,
        verdict: "SECURITY_POSTURE_PARTIALLY_IMPROVED",
      },
      reports: [],
    });
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("submits arbitrary workspace-relative baseline and target paths", async () => {
    render(<ComparePage />);

    const baselineInput = await screen.findByRole("combobox", {
      name: "Baseline repository path",
    });

    const targetInput = screen.getByRole("combobox", {
      name: "Target repository path",
    });

    fireEvent.change(baselineInput, {
      target: { value: "repo-a-fastapi-template" },
    });

    fireEvent.change(targetInput, {
      target: { value: "repo-b-vulnreach" },
    });

    expect(baselineInput).toHaveValue("repo-a-fastapi-template");
    expect(targetInput).toHaveValue("repo-b-vulnreach");

    fireEvent.click(
      screen.getByRole("button", {
        name: "Compare posture",
      }),
    );

    await waitFor(() => {
      expect(apiMocks.runComparison).toHaveBeenCalledTimes(1);
    });

    expect(apiMocks.runComparison).toHaveBeenCalledWith(
      "csrf-test-token",
      "repo-a-fastapi-template",
      "repo-b-vulnreach",
      "repo-a-fastapi-template",
      "repo-b-vulnreach",
    );

    expect(await screen.findByText("+11")).toBeInTheDocument();
    expect(screen.getByText("12.94%")).toBeInTheDocument();
    expect(screen.getByText("Partially improved")).toBeInTheDocument();
  });
});
