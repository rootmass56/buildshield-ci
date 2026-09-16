import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  Boxes,
  FileSearch,
  Files,
  GitCompareArrows,
  History,
  Radar,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router-dom";

import { ApiError, getHistory, getReports } from "../api/client";
import { ErrorPanel, MetricCard } from "../components/Ui";
import type { HistoryRecord } from "../types/api";

const quickActions = [
  {
    to: "/app/scanner",
    title: "Run security scan",
    detail: "Analyze repository controls and evaluate policy.",
    icon: FileSearch,
  },
  {
    to: "/app/inventory",
    title: "Dependency inventory",
    detail: "Inspect npm and Python dependency metadata.",
    icon: Boxes,
  },
  {
    to: "/app/vulnerability-intelligence",
    title: "OSV intelligence",
    detail: "Check pinned versions against vulnerability intelligence.",
    icon: Radar,
  },
  {
    to: "/app/compare",
    title: "Compare posture",
    detail: "Measure security improvement between repositories.",
    icon: GitCompareArrows,
  },
] as const;

export function OverviewPage() {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [reports, setReports] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([getHistory(5), getReports()])
      .then(([historyResponse, reportResponse]) => {
        setHistory(historyResponse.history);
        setReports(reportResponse.reports.length);
      })
      .catch((caughtError) =>
        setError(
          caughtError instanceof ApiError
            ? caughtError.message
            : "Unable to load overview.",
        ),
      );
  }, []);

  const latest = history[0] ?? null;
  const average = useMemo(
    () =>
      history.length
        ? Math.round(
            history.reduce((total, item) => total + item.security_score, 0) /
              history.length,
          )
        : null,
    [history],
  );

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Overview</span>
          <h2>Security posture overview</h2>
          <p>
            Monitor repository risk, policy outcomes, and recent analysis from
            one protected workspace.
          </p>
        </div>
      </div>

      {error ? <ErrorPanel message={error} /> : null}

      <div className="metric-grid">
        <MetricCard
          label="Latest score"
          value={latest ? `${latest.security_score}/100` : "—"}
          detail={latest?.risk_level ?? "No completed scans"}
          icon={<Activity size={18} />}
        />
        <MetricCard
          label="Latest findings"
          value={latest?.findings_count ?? "—"}
          detail={latest?.target_path ?? "No scan history yet"}
          icon={<ShieldCheck size={18} />}
        />
        <MetricCard
          label="Recent average"
          value={average === null ? "—" : `${average}/100`}
          detail={`${history.length} recent ${history.length === 1 ? "scan" : "scans"}`}
          icon={<History size={18} />}
        />
        <MetricCard
          label="Reports"
          value={reports}
          detail="Available security artifacts"
          icon={<Files size={18} />}
        />
      </div>

      <div className="section-heading-row">
        <div>
          <span className="section-kicker">Actions</span>
          <h3>Start an analysis</h3>
        </div>
      </div>

      <div className="quick-grid">
        {quickActions.map(({ to, title, detail, icon: Icon }) => (
          <Link className="quick-card" to={to} key={to}>
            <div className="quick-card-icon" aria-hidden="true">
              <Icon size={19} strokeWidth={1.9} />
            </div>
            <div className="quick-card-copy">
              <strong>{title}</strong>
              <span>{detail}</span>
            </div>
            <ArrowRight className="quick-card-arrow" size={17} aria-hidden="true" />
          </Link>
        ))}
      </div>

      <article className="benchmark-panel">
        <div className="benchmark-heading">
          <div>
            <span className="eyebrow">Controlled benchmark</span>
            <h3>Verified hardening delta</h3>
            <p>
              This synthetic 5 → 100 benchmark is a regression anchor, not an
              expected score for routine repositories. Day-to-day scans can land
              anywhere across the risk range.
            </p>
          </div>
          <span className="verified-badge">
            <ShieldCheck size={15} aria-hidden="true" />
            Verified
          </span>
        </div>

        <div className="benchmark-grid">
          <div className="benchmark-state benchmark-vulnerable">
            <ShieldAlert size={20} aria-hidden="true" />
            <div>
              <span>Vulnerable baseline</span>
              <strong>5 / 100</strong>
              <small>22 findings</small>
            </div>
          </div>

          <div className="benchmark-arrow" aria-hidden="true">
            <ArrowRight size={22} />
          </div>

          <div className="benchmark-state benchmark-secure">
            <ShieldCheck size={20} aria-hidden="true" />
            <div>
              <span>Hardened target</span>
              <strong>100 / 100</strong>
              <small>0 findings</small>
            </div>
          </div>
        </div>
      </article>
    </section>
  );
}
