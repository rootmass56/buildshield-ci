import { CheckCircle2, GitBranch, ShieldCheck } from "lucide-react";

const controls = [
  "Third-party GitHub Actions are pinned to immutable commit SHAs.",
  "CI enforces regression, quality, reproducibility, and security gates.",
  "SARIF integrates scanner results with GitHub Code Scanning.",
  "Security reports are retained as workflow artifacts for review.",
];

export function CicdPage() {
  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">CI/CD</span>
          <h2>Pipeline security posture</h2>
          <p>
            Review the controls BuildShield-CI applies to its own software
            delivery pipeline.
          </p>
        </div>
      </div>

      <div className="split-layout">
        <article className="information-card">
          <div className="card-heading">
            <div className="card-heading-icon" aria-hidden="true">
              <GitBranch size={18} />
            </div>
            <div>
              <span className="section-kicker">Delivery controls</span>
              <h3>Verified pipeline safeguards</h3>
            </div>
          </div>
          <div className="check-list">
            {controls.map((control) => (
              <div key={control}>
                <CheckCircle2 size={16} aria-hidden="true" />
                <span>{control}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="information-card release-assurance-card">
          <div className="card-heading">
            <div className="card-heading-icon" aria-hidden="true">
              <ShieldCheck size={18} />
            </div>
            <div>
              <span className="section-kicker">Release assurance</span>
              <h3>Security gates are part of the build</h3>
            </div>
          </div>
          <p>
            BuildShield-CI validates locked dependencies, static analysis,
            testing, package reproducibility, frontend quality, and controlled
            security posture before release acceptance.
          </p>
        </article>
      </div>
    </section>
  );
}
