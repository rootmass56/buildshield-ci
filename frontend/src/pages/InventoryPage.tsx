import { FormEvent, useState } from "react";
import { Boxes } from "lucide-react";

import { ApiError, runInventory } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import {
  ErrorPanel,
  MetricCard,
  ReportLinks,
  StatusBadge,
} from "../components/Ui";
import type { InventoryResponse } from "../types/api";

export function InventoryPage() {
  const auth = useAuth();
  const [target, setTarget] = useState("samples/realistic-repo");
  const [result, setResult] = useState<InventoryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!auth.csrfToken) {
      return;
    }

    try {
      setResult(await runInventory(auth.csrfToken, target));
      setError(null);
    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
          ? caughtError.message
          : "Inventory generation failed.",
      );
    }
  }

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">Inventory</span>
          <h2>Dependency inventory</h2>
          <p>
            Inspect package metadata, version pinning, ecosystems, and internal
            package candidates across the selected repository.
          </p>
        </div>
      </div>

      <form className="inline-form control-strip" onSubmit={(event) => void submit(event)}>
        <div className="control-strip-icon" aria-hidden="true">
          <Boxes size={18} />
        </div>
        <label className="grow">
          Repository path
          <input value={target} onChange={(event) => setTarget(event.target.value)} />
        </label>
        <button className="primary-button">Generate inventory</button>
      </form>

      {error ? <ErrorPanel message={error} /> : null}

      {result ? (
        <>
          <div className="metric-grid scan-metrics">
            <MetricCard
              label="Dependencies"
              value={result.inventory.summary.total_dependencies}
              detail={result.inventory.summary.ecosystems_detected.join(", ")}
            />
            <MetricCard
              label="Pinned"
              value={result.inventory.summary.pinned_dependencies}
              detail="Exact versions"
            />
            <MetricCard
              label="Unpinned"
              value={result.inventory.summary.unpinned_dependencies}
              detail="Review targets"
            />
            <MetricCard
              label="Internal candidates"
              value={result.inventory.summary.internal_candidate_dependencies}
              detail="Dependency-confusion review"
            />
          </div>

          <div className="table-panel">
            <table>
              <thead>
                <tr>
                  <th>Package</th>
                  <th>Ecosystem</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {result.inventory.dependencies.map((dependency, index) => (
                  <tr key={`${dependency.name}-${index}`}>
                    <td>{dependency.name}</td>
                    <td>{dependency.ecosystem}</td>
                    <td>{dependency.declared_version ?? "—"}</td>
                    <td>
                      <StatusBadge
                        value={dependency.is_pinned ? "PINNED" : "REVIEW"}
                        positive={dependency.is_pinned}
                      />
                    </td>
                    <td>
                      <code>{dependency.file_path}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ReportLinks reports={result.reports} />
        </>
      ) : null}
    </section>
  );
}
