import { EmptyPanel, MetricCard, StatusBadge } from "../components/Ui";
import { useScanState } from "../state/ScanContext";

export function PolicyPage() {
  const { latestScan } = useScanState();
  const policy = latestScan?.policy_evaluation;

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Policy</span>
          <h2>Policy-as-code decision</h2>
          <p>
            Review the minimum score, fail-on severities, and policy violations
            evaluated against the latest scan.
          </p>
        </div>
        {policy ? (
          <StatusBadge
            value={policy.passed ? "PASSED" : "FAILED"}
            positive={policy.passed}
          />
        ) : null}
      </div>

      {!policy ? (
        <EmptyPanel
          title="No policy decision loaded"
          detail="Run a security scan with a policy file to evaluate the gate."
        />
      ) : (
        <>
          <div className="policy-file-strip">
            <span>Policy file</span>
            <code>{policy.policy_file}</code>
          </div>

          <div className="metric-grid scan-metrics">
            <MetricCard
              label="Actual score"
              value={`${policy.actual_score}/100`}
              detail="Repository score"
            />
            <MetricCard
              label="Minimum score"
              value={`${policy.minimum_score}/100`}
              detail="Required score"
            />
            <MetricCard
              label="Violations"
              value={policy.violations.length}
              detail="Policy failures"
            />
            <MetricCard
              label="Fail-on"
              value={policy.fail_on_severities.length}
              detail={policy.fail_on_severities.join(", ") || "None"}
            />
          </div>

          {!policy.violations.length ? (
            <EmptyPanel
              title="No policy violations"
              detail="The latest policy evaluation did not produce violations."
            />
          ) : (
            <div className="simple-list">
              {policy.violations.map((violation, index) => (
                <article
                  className="list-row"
                  key={`${violation.policy_id}-${index}`}
                >
                  <div>
                    <strong>{violation.policy_id}</strong>
                    <p>{violation.message}</p>
                  </div>
                  <StatusBadge value={violation.severity} />
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
