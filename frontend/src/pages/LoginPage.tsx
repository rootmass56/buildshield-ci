import { FormEvent, useState } from "react";
import {
  LockKeyhole,
  ScanSearch,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const trustPoints = [
  {
    icon: ScanSearch,
    title: "Workspace-contained analysis",
    detail: "Repository operations stay inside the approved analysis boundary.",
  },
  {
    icon: LockKeyhole,
    title: "Authenticated operations",
    detail: "Protected administrative sessions and CSRF validation are enforced.",
  },
  {
    icon: Workflow,
    title: "Reproducible security gates",
    detail: "Policy, CI/CD, reports, and release checks share one security model.",
  },
] as const;

export function LoginPage() {
  const auth = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (auth.authenticated) {
    return <Navigate to="/app" replace />;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await auth.login(username, password);
      navigate("/app", { replace: true });
    } catch (caughtError) {
      if (caughtError instanceof ApiError) {
        setError(caughtError.message);
      } else {
        setError("Unable to sign in. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-hero" aria-label="BuildShield-CI">
        <div className="login-brand-row">
          <div className="brand-mark large" aria-hidden="true">
            <ShieldCheck size={30} strokeWidth={2} />
          </div>
          <div>
            <span className="eyebrow">BuildShield-CI</span>
            <span className="login-product-subtitle">Supply-chain security platform</span>
          </div>
        </div>

        <h1>Security analysis for the software delivery pipeline.</h1>
        <p className="login-lead">
          Inspect dependencies, CI/CD workflows, container hardening, policy
          gates, vulnerability intelligence, and security reports from one
          controlled workspace.
        </p>

        <div className="login-trust-grid">
          {trustPoints.map(({ icon: Icon, title, detail }) => (
            <article className="login-trust-item" key={title}>
              <div className="login-trust-icon" aria-hidden="true">
                <Icon size={18} />
              </div>
              <div>
                <strong>{title}</strong>
                <span>{detail}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div className="login-card-header">
            <span className="eyebrow">Administrator access</span>
            <h2>Sign in to BuildShield-CI</h2>
            <p>
              Use the administrator credentials configured for this secured
              instance.
            </p>
          </div>

          <form onSubmit={(event) => void handleSubmit(event)}>
            <label>
              Username
              <input
                name="username"
                autoComplete="username"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
              />
            </label>

            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>

            {error ? (
              <div className="form-error" role="alert">
                {error}
              </div>
            ) : null}

            <button
              className="primary-button login-submit"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Signing in…" : "Open security workspace"}
            </button>
          </form>

          <div className="login-card-footer">
            <LockKeyhole size={15} aria-hidden="true" />
            <span>Protected administrative session</span>
          </div>
        </div>
      </section>
    </main>
  );
}
