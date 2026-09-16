import { useMemo, useState } from "react";
import { Search } from "lucide-react";

import { EmptyPanel, SeverityBadge } from "../components/Ui";
import { useScanState } from "../state/ScanContext";

export function FindingsPage() {
  const { latestScan } = useScanState();
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("ALL");

  const findings = useMemo(
    () =>
      latestScan?.findings.filter(
        (finding) =>
          (severity === "ALL" || finding.severity === severity) &&
          (!query.trim() ||
            `${finding.rule_id} ${finding.title} ${finding.category} ${finding.evidence.file_path}`
              .toLowerCase()
              .includes(query.toLowerCase())),
      ) ?? [],
    [latestScan, query, severity],
  );

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Findings</span>
          <h2>Security findings</h2>
          <p>
            Review rule matches, evidence, impact, and remediation from the
            latest repository scan.
          </p>
        </div>
      </div>

      {!latestScan ? (
        <EmptyPanel
          title="No scan loaded"
          detail="Run a repository security scan to populate findings."
        />
      ) : (
        <>
          <div className="filter-bar findings-filter-bar">
            <label className="search-field">
              <Search size={16} aria-hidden="true" />
              <input
                aria-label="Search findings"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search rule, title, category, or file"
              />
            </label>
            <select
              aria-label="Filter severity"
              value={severity}
              onChange={(event) => setSeverity(event.target.value)}
            >
              {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"].map(
                (value) => (
                  <option key={value}>{value}</option>
                ),
              )}
            </select>
            <span className="filter-count" aria-live="polite">
              {findings.length} of {latestScan.findings.length}
            </span>
          </div>

          {!findings.length ? (
            <EmptyPanel
              title="No findings match this filter"
              detail="Adjust the search term or severity filter."
            />
          ) : (
            <div className="finding-list">
              {findings.map((finding, index) => (
                <details
                  className="finding-card"
                  key={`${finding.rule_id}-${index}`}
                >
                  <summary>
                    <div>
                      <strong>
                        {finding.rule_id}: {finding.title}
                      </strong>
                      <span>
                        {finding.category} · {finding.confidence} confidence
                      </span>
                    </div>
                    <SeverityBadge value={finding.severity} />
                  </summary>

                  <div className="finding-body">
                    <p>{finding.description}</p>
                    <p>
                      <strong>Impact:</strong> {finding.impact}
                    </p>
                    <code>
                      {finding.evidence.file_path}
                      {finding.evidence.line_number
                        ? `:${finding.evidence.line_number}`
                        : ""}
                    </code>
                    {finding.evidence.snippet ? (
                      <pre>{finding.evidence.snippet}</pre>
                    ) : null}
                    <p>
                      <strong>Remediation:</strong> {finding.remediation}
                    </p>
                  </div>
                </details>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}
