import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2, FileSearch, LockKeyhole, ShieldCheck } from "lucide-react";

import { ApiError, getSampleRepositories, runScan } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import {
  ErrorPanel,
  MetricCard,
  ReportLinks,
  SeverityBadge,
  StatusBadge,
} from "../components/Ui";
import { useScanState } from "../state/ScanContext";
import type { SampleRepository } from "../types/api";

function displayPathName(value: string): string {
  const parts = value.split(/[\\/]/).filter(Boolean);
  return parts.at(-1) ?? value;
}

const executionControls = [
  "Workspace path containment",
  "Authenticated administrative session",
  "CSRF-protected state-changing requests",
];

export function ScannerPage() {
  const auth = useAuth();
  const scan = useScanState();
  const [repos, setRepos] = useState<SampleRepository[]>([]);
  const [target, setTarget] = useState("samples/realistic-repo");
  const [policy, setPolicy] = useState("buildshield-policy.yml");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getSampleRepositories()
      .then((response) => {
        setRepos(response.repositories);
        setPolicy(response.default_policy);
      })
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
      setError("Missing CSRF state.");
      return;
    }

    setBusy(true);
    setError(null);

    try {
      scan.setLatestScan(
        await runScan(
          auth.csrfToken,
          target,
          policy.trim() || null,
          ["json", "md", "html", "sarif"],
        ),
      );
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Scan failed.");
    } finally {
      setBusy(false);
    }
  }

  const result = scan.latestScan;
  const selectedRepository = repos.find((repo) => repo.path === target) ?? null;

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Scanner</span>
          <h2>Repository security scan</h2>
          <p>
            Analyze a repository inside the approved workspace and evaluate its
            policy gate in one controlled operation.
          </p>
        </div>
      </div>

      <div className="split-layout scanner-layout">
        <form className="control-card" onSubmit={(event) => void submit(event)}>
          <div className="card-heading">
            <div className="card-heading-icon" aria-hidden="true">
              <FileSearch size={18} />
            </div>
            <div>
              <h3>Scan configuration</h3>
              <p>Select a repository target and optional policy file.</p>
            </div>
          </div>

          <label>
            Repository preset
            <select value={target} onChange={(event) => setTarget(event.target.value)}>
              {repos.map((repo) => (
                <option key={repo.path} value={repo.path}>
                  {repo.label}
                </option>
              ))}
            </select>
            {selectedRepository ? (
              <span className="field-hint">{selectedRepository.description}</span>
            ) : null}
          </label>

          <label>
            Workspace path
            <input
              aria-label="Workspace path"
              value={target}
              onChange={(event) => setTarget(event.target.value)}
            />
          </label>

          <label>
            Policy file
            <input value={policy} onChange={(event) => setPolicy(event.target.value)} />
          </label>

          {error ? <ErrorPanel message={error} /> : null}

          <button className="primary-button" disabled={busy}>
            <FileSearch size={16} aria-hidden="true" />
            {busy ? "Scanning repository…" : "Run security scan"}
          </button>
        </form>

        <article className="information-card security-controls-card">
          <div className="card-heading">
            <div className="card-heading-icon" aria-hidden="true">
              <LockKeyhole size={18} />
            </div>
            <div>
              <span className="section-kicker">Security controls</span>
              <h3>Protected execution boundary</h3>
            </div>
          </div>

          <p>
            Repository analysis runs with the same security boundaries enforced
            by the production dashboard.
          </p>

          <div className="check-list compact">
            {executionControls.map((control) => (
              <div key={control}>
                <CheckCircle2 size={16} aria-hidden="true" />
                <span>{control}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      {result ? (
        <>
          <div className="section-heading-row results-heading">
            <div>
              <span className="section-kicker">Latest result</span>
              <h3>Security assessment</h3>
            </div>
            <StatusBadge
              value={`Risk · ${result.summary.risk_level}`}
              positive={result.summary.findings_count === 0}
            />
          </div>

          <div className="metric-grid scan-metrics scanner-result-metrics">
            <MetricCard
              label="Security score"
              value={`${result.summary.security_score}/100`}
              detail={result.summary.risk_level}
              icon={<ShieldCheck size={18} />}
            />
            <MetricCard
              label="Findings"
              value={result.summary.findings_count}
              detail={`${result.summary.files_scanned} files scanned`}
            />
            <MetricCard
              label="Build gate"
              value={result.risk_profile.build_gate_status}
              detail={result.risk_profile.build_gate_reason}
            />
            <MetricCard
              label="Policy"
              value={result.policy_evaluation?.passed ? "PASSED" : "FAILED"}
              detail={
                result.policy_evaluation?.policy_file
                  ? displayPathName(result.policy_evaluation.policy_file)
                  : "Not evaluated"
              }
            />
          </div>

          <div className="panel result-panel">
            <div className="panel-heading">
              <div>
                <span className="section-kicker">Target</span>
                <h3>{result.target_path}</h3>
              </div>
            </div>

            <div className="severity-summary">
              <SeverityBadge value={`CRITICAL ${result.summary.critical_count}`} />
              <SeverityBadge value={`HIGH ${result.summary.high_count}`} />
              <SeverityBadge value={`MEDIUM ${result.summary.medium_count}`} />
              <SeverityBadge value={`LOW ${result.summary.low_count}`} />
            </div>

            <ReportLinks reports={result.reports} />
          </div>
        </>
      ) : null}
    </section>
  );
}
