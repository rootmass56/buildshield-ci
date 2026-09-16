import { useEffect, useState } from "react";
import { Boxes, FileCode2, HeartPulse, ShieldCheck } from "lucide-react";

import { ApiError, getHealth } from "../api/client";
import { ErrorPanel, LoadingPanel, StatusBadge } from "../components/Ui";
import type { HealthResponse } from "../types/api";

export function AboutPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getHealth()
      .then(setHealth)
      .catch((caughtError) =>
        setError(
          caughtError instanceof ApiError
            ? caughtError.message
            : "Unable to read service health.",
        ),
      );
  }, []);

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">About</span>
          <h2>BuildShield-CI</h2>
          <p>
            Production-style DevSecOps tooling for software supply-chain risk
            analysis, policy enforcement, and release security evidence.
          </p>
        </div>
      </div>

      {error ? <ErrorPanel message={error} /> : null}
      {!health && !error ? <LoadingPanel message="Loading service information…" /> : null}

      {health ? (
        <div className="about-grid">
          <article className="about-stat-card">
            <div className="about-stat-icon">
              <ShieldCheck size={19} />
            </div>
            <span>Product</span>
            <strong>{health.product}</strong>
            <small>Version {health.version}</small>
          </article>

          <article className="about-stat-card">
            <div className="about-stat-icon">
              <HeartPulse size={19} />
            </div>
            <span>API status</span>
            <strong>Operational</strong>
            <StatusBadge value={health.status} positive={health.status === "ok"} />
          </article>

          <article className="about-stat-card">
            <div className="about-stat-icon">
              <Boxes size={19} />
            </div>
            <span>Analyzers</span>
            <strong>4 families</strong>
            <small>npm · Python · GitHub Actions · Dockerfile</small>
          </article>

          <article className="about-stat-card">
            <div className="about-stat-icon">
              <FileCode2 size={19} />
            </div>
            <span>Outputs</span>
            <strong>4 formats</strong>
            <small>JSON · Markdown · HTML · SARIF</small>
          </article>
        </div>
      ) : null}
    </section>
  );
}
