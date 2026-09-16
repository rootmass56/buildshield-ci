import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ApiError, getHistory, getTrend } from "../api/client";
import {
  EmptyPanel,
  ErrorPanel,
  LoadingPanel,
  MetricCard,
  StatusBadge,
} from "../components/Ui";
import type { HistoryRecord } from "../types/api";

export function HistoryPage() {
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [trend, setTrend] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void Promise.all([getHistory(20), getTrend(20)])
      .then(([historyResponse, trendResponse]) => {
        setHistory(historyResponse.history);
        setTrend(trendResponse.trend);
      })
      .catch((caughtError) =>
        setError(
          caughtError instanceof ApiError
            ? caughtError.message
            : "Unable to load history.",
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  return (
    <section className="page-section">
      <div className="page-heading">
        <div>
          <span className="eyebrow">History</span>
          <h2>Security score trends</h2>
          <p>Review persisted repository scan outcomes and score movement.</p>
        </div>
      </div>

      {loading ? <LoadingPanel message="Loading scan history…" /> : null}
      {error ? <ErrorPanel message={error} /> : null}
      {!loading && !error && !history.length ? (
        <EmptyPanel
          title="No scan history yet"
          detail="Run a repository security scan to start building trend data."
        />
      ) : null}

      {!loading && !error && history.length ? (
        <>
          <div className="metric-grid history-summary-grid">
            <MetricCard
              label="Latest score"
              value={`${history[0].security_score}/100`}
              detail={history[0].target_path}
            />
            <MetricCard
              label="Recorded runs"
              value={history.length}
              detail="Persisted scan outcomes"
            />
            <MetricCard
              label="Latest findings"
              value={history[0].findings_count}
              detail={`${history[0].critical_count} critical · ${history[0].high_count} high`}
            />
            <MetricCard
              label="Latest policy"
              value={history[0].policy_status}
              detail={history[0].build_gate_status === "PASSED" ? "Build gate passed" : "Build gate blocked"}
            />
          </div>

          <div className="chart-panel">
            <div className="panel-title-row">
              <div>
                <span className="section-kicker">Trend</span>
                <h3>Security score</h3>
              </div>
              <span className="chart-scale">0–100</span>
            </div>
            <div className="chart-canvas">
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={trend} margin={{ top: 12, right: 12, left: -10, bottom: 0 }}>
                  <CartesianGrid
                    stroke="rgba(148, 163, 184, 0.12)"
                    vertical={false}
                  />
                  <XAxis
                    dataKey="id"
                    tickFormatter={(value) => `#${value}`}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#7f93ac", fontSize: 12 }}
                  />
                  <YAxis
                    domain={[0, 100]}
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: "#7f93ac", fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#0f1b2c",
                      border: "1px solid rgba(148, 163, 184, 0.16)",
                      borderRadius: "10px",
                      color: "#e8eef6",
                      boxShadow: "0 12px 34px rgba(0, 0, 0, 0.24)",
                    }}
                    labelStyle={{ color: "#8ea0b5" }}
                  />
                  <Line
                    type="monotone"
                    dataKey="security_score"
                    stroke="#54d2b4"
                    strokeWidth={2.5}
                    dot={{ r: 3.5, fill: "#54d2b4", strokeWidth: 0 }}
                    activeDot={{ r: 4.5, fill: "#54d2b4", strokeWidth: 0 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="table-panel">
            <table>
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Target</th>
                  <th>Score</th>
                  <th>Risk</th>
                  <th>Findings</th>
                  <th>Policy</th>
                </tr>
              </thead>
              <tbody>
                {history.map((record) => (
                  <tr key={record.id}>
                    <td>
                      <code>{record.run_id}</code>
                    </td>
                    <td>{record.target_path}</td>
                    <td>{record.security_score}/100</td>
                    <td>
                      <StatusBadge
                        value={record.risk_level}
                        positive={record.findings_count === 0}
                      />
                    </td>
                    <td>{record.findings_count}</td>
                    <td>{record.policy_status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </section>
  );
}
