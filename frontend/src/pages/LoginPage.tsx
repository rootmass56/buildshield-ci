import { FormEvent, useState } from "react";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

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
        <div className="brand-mark large" aria-hidden="true">
          <ShieldCheck size={36} />
        </div>
        <span className="eyebrow">BuildShield-CI</span>
        <h1>Secure the software supply chain before it reaches production.</h1>
        <p>
          Analyze dependency-confusion exposure, CI/CD workflow risks,
          Docker hardening, vulnerable dependencies, policy gates and
          security reports from one protected workspace.
        </p>

        <div className="security-proof">
          <LockKeyhole size={20} aria-hidden="true" />
          <div>
            <strong>Protected administrative session</strong>
            <span>HttpOnly session cookie + CSRF validation</span>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div>
            <span className="eyebrow">Administrator access</span>
            <h2>Sign in</h2>
            <p>
              Use the administrator credentials configured for this
              BuildShield-CI instance.
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
              className="primary-button"
              type="submit"
              disabled={submitting}
            >
              {submitting ? "Signing in…" : "Open security dashboard"}
            </button>
          </form>
        </div>
      </section>
    </main>
  );
}
