import type { ReactNode } from "react";
import {
  AlertTriangle,
  CircleDashed,
  FileDown,
  Inbox,
} from "lucide-react";

import type { ReportLink } from "../types/api";
import { normalizeEnumLabel } from "../utils/security";

export function reportDisplayName(filename: string): string {
  const normalized = filename.toLowerCase();

  if (normalized.endsWith(".sarif")) {
    return "SARIF report";
  }

  if (normalized.endsWith(".html")) {
    return "HTML report";
  }

  if (normalized.endsWith(".md")) {
    return "Markdown report";
  }

  if (normalized.endsWith(".json")) {
    return normalized.includes("inventory")
      ? "Inventory JSON"
      : "JSON report";
  }

  return "Security artifact";
}

export function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="message-panel danger" role="alert">
      <AlertTriangle size={18} aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}

export function LoadingPanel({ message = "Loading…" }: { message?: string }) {
  return (
    <div className="message-panel" aria-live="polite">
      <CircleDashed className="spin" size={18} aria-hidden="true" />
      <span>{message}</span>
    </div>
  );
}

export function EmptyPanel({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="empty-panel">
      <div className="empty-panel-icon" aria-hidden="true">
        <Inbox size={22} />
      </div>
      <strong>{title}</strong>
      <span>{detail}</span>
    </div>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: ReactNode;
  detail: string;
  icon?: ReactNode;
}) {
  return (
    <article className="metric-card">
      <div className="metric-card-header">
        {icon ? <div className="metric-icon">{icon}</div> : null}
        <span>{label}</span>
      </div>
      <strong className="metric-value">{value}</strong>
      <p>{detail}</p>
    </article>
  );
}

export function SeverityBadge({ value }: { value: string }) {
  const normalized = normalizeEnumLabel(value);
  const first = normalized.split(" ")[0].toLowerCase();

  return (
    <span className={`severity-badge severity-${first}`}>
      {normalized}
    </span>
  );
}

export function StatusBadge({
  value,
  positive = false,
}: {
  value: string;
  positive?: boolean;
}) {
  return (
    <span className={positive ? "status-badge positive" : "status-badge"}>
      {normalizeEnumLabel(value)}
    </span>
  );
}

export function ReportLinks({ reports }: { reports: ReportLink[] }) {
  if (!reports.length) {
    return null;
  }

  return (
    <div className="report-links">
      {reports.map((report) => (
        <a
          key={`${report.run_id}-${report.filename}`}
          href={report.download_url}
          className="report-link"
        >
          <FileDown size={15} aria-hidden="true" />
          <span title={report.filename}>{reportDisplayName(report.filename)}</span>
        </a>
      ))}
    </div>
  );
}
