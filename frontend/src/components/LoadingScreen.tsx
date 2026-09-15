import { ShieldCheck } from "lucide-react";

export function LoadingScreen() {
  return (
    <main className="loading-screen" aria-busy="true" aria-live="polite">
      <div className="loading-mark" aria-hidden="true">
        <ShieldCheck size={28} />
      </div>
      <p>Securing workspace…</p>
    </main>
  );
}
