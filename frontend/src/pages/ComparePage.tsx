import { FormEvent, useEffect, useState } from "react";
import { ArrowRight, GitCompareArrows } from "lucide-react";

import { ApiError, getSampleRepositories, runComparison } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import {
  ErrorPanel,
  MetricCard,
  ReportLinks,
  StatusBadge,
} from "../components/Ui";
import type { ComparisonResponse, SampleRepository } from "../types/api";
import { normalizeEnumLabel } from "../utils/security";

function sentenceCase(value: string): string {
  const normalized = normalizeEnumLabel(value).toLowerCase();
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function verdictHeadline(value: string): string {
  switch (value) {
    case "SECURITY_POSTURE_SIGNIFICANTLY_IMPROVED":
      return "Significantly improved";
    case "SECURITY_POSTURE_PARTIALLY_IMPROVED":
      return "Partially improved";
    case "NO_MEASURABLE_SECURITY_CHANGE":
      return "No measurable change";
    case "SECURITY_POSTURE_REGRESSED":
      return "Regressed";
    default:
      return sentenceCase(value);
  }
}

export function ComparePage() {
  const auth = useAuth();
  const [repos, setRepos] = useState<SampleRepository[]>([]);
  const [baseline, setBaseline] = useState("samples/vulnerable-repo");
  const [target, setTarget] = useState("samples/realistic-repo");
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getSampleRepositories()
      .then((response) => setRepos(response.repositories))
      .catch((caughtError) =>
        setError(
          caughtError instanceof ApiError
            ? caughtError.message
            : "Unable to load repository presets.",
        ),
      );
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!auth.csrfToken) {
      return;
    }

    const baselinePath = baseline.trim();
    const targetPath = target.trim();

    if (!baselinePath || !targetPath) {
      setError("Baseline and target repository paths are required.");
      return;
    }

    const baselineRepo = repos.find((repo) => repo.path === baselinePath);
    const targetRepo = repos.find((repo) => repo.path === targetPath);

    try {
      setResult(
        await runComparison(
          auth.csrfToken,
          baselinePath,
          targetPath,
          baselineRepo?.label ?? baselinePath,
          targetRepo?.label ?? targetPath,
        ),
      );
      setError(null);
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "Comparison failed.",
      );
    }
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Compare</span>
          <h2>Security posture comparison</h2>
          <p>
            Compare repository states inside the approved workspace without
            treating a perfect score as the expected outcome for every
            application.
          </p>
        </div>
      </div>

      <form
        className="compare-form control-strip"
        onSubmit={(event) => void submit(event)}
      >
        <div className="control-strip-icon" aria-hidden="true">
          <GitCompareArrows size={18} />
        </div>

        <label>
          Baseline
          <input
            aria-label="Baseline repository path"
            list="baseline-repository-presets"
            value={baseline}
            onChange={(event) => setBaseline(event.target.value)}
            placeholder="repo-a-fastapi-template"
            autoComplete="off"
            required
          />
          <datalist id="baseline-repository-presets">
            {repos.map((repo) => (
              <option key={repo.path} value={repo.path}>
                {repo.label}
              </option>
            ))}
          </datalist>
          <span className="field-hint">
            Select a preset or enter a workspace-relative repository path.
          </span>
        </label>

        <div className="compare-direction" aria-hidden="true">
          <ArrowRight size={17} />
        </div>

        <label>
          Target
          <input
            aria-label="Target repository path"
            list="target-repository-presets"
            value={target}
            onChange={(event) => setTarget(event.target.value)}
            placeholder="repo-b-vulnreach"
            autoComplete="off"
            required
          />
          <datalist id="target-repository-presets">
            {repos.map((repo) => (
              <option key={repo.path} value={repo.path}>
                {repo.label}
              </option>
            ))}
          </datalist>
          <span className="field-hint">
            Select a preset or enter a workspace-relative repository path.
          </span>
        </label>

        <button className="primary-button">Compare posture</button>
      </form>

      {error ? <ErrorPanel message={error} /> : null}

      {result ? (
        <>
          <div className="metric-grid scan-metrics">
            <MetricCard
              label="Score improvement"
              value={`${result.comparison.score_delta >= 0 ? "+" : ""}${result.comparison.score_delta}`}
              detail={`${result.comparison.baseline.summary.security_score} → ${result.comparison.target.summary.security_score}`}
            />
            <MetricCard
              label="Findings reduced"
              value={result.comparison.findings_reduced}
              detail={`${result.comparison.baseline.summary.findings_count} → ${result.comparison.target.summary.findings_count}`}
            />
            <MetricCard
              label="Risk reduction"
              value={`${result.comparison.risk_reduction_percentage}%`}
              detail="Selected repository states"
            />
            <MetricCard
              label="Verdict"
              value={verdictHeadline(result.comparison.verdict)}
              detail={sentenceCase(result.comparison.verdict)}
            />
          </div>

          <div className="comparison-grid">
            <article className="panel comparison-state">
              <span className="section-kicker">Baseline</span>
              <h3>{result.comparison.baseline_label}</h3>
              <strong>
                {result.comparison.baseline.summary.security_score}/100
              </strong>
              <StatusBadge
                value={result.comparison.baseline.summary.risk_level}
              />
            </article>

            <article className="panel comparison-state comparison-state-target">
              <span className="section-kicker">Target</span>
              <h3>{result.comparison.target_label}</h3>
              <strong>
                {result.comparison.target.summary.security_score}/100
              </strong>
              <StatusBadge
                value={result.comparison.target.summary.risk_level}
                positive={result.comparison.target.summary.findings_count === 0}
              />
            </article>
          </div>

          <ReportLinks reports={result.reports} />
        </>
      ) : null}
    </section>
  );
}
