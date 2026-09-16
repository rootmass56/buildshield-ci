import { ShieldCheck } from "lucide-react";

export function LoadingScreen() {
  return (
    <main className="loading-screen" aria-busy="true" aria-live="polite">
      <div className="loading-mark" aria-hidden="true">
        <ShieldCheck size={25} strokeWidth={2} />
      </div>
      <p>Initializing protected workspace…</p>
    </main>
  );
}
