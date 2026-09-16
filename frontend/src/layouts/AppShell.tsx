import {
  Boxes,
  FileSearch,
  Files,
  GitBranch,
  GitCompareArrows,
  History,
  Info,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Radar,
  ShieldCheck,
  SlidersHorizontal,
} from "lucide-react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

type NavItem = {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
  end?: boolean;
};

const analysisNav: NavItem[] = [
  { label: "Overview", to: "/app", icon: LayoutDashboard, end: true },
  { label: "Scanner", to: "/app/scanner", icon: FileSearch },
  { label: "Findings", to: "/app/findings", icon: ListChecks },
  { label: "Policy", to: "/app/policy", icon: SlidersHorizontal },
  { label: "Inventory", to: "/app/inventory", icon: Boxes },
  { label: "OSV Intel", to: "/app/vulnerability-intelligence", icon: Radar },
  { label: "Compare", to: "/app/compare", icon: GitCompareArrows },
];

const operationsNav: NavItem[] = [
  { label: "History", to: "/app/history", icon: History },
  { label: "Reports", to: "/app/reports", icon: Files },
  { label: "CI/CD", to: "/app/cicd", icon: GitBranch },
  { label: "About", to: "/app/about", icon: Info },
];

const routeLabels: Record<string, string> = {
  "/app": "Overview",
  "/app/scanner": "Scanner",
  "/app/findings": "Findings",
  "/app/policy": "Policy",
  "/app/inventory": "Inventory",
  "/app/vulnerability-intelligence": "OSV Intelligence",
  "/app/compare": "Compare",
  "/app/history": "History",
  "/app/reports": "Reports",
  "/app/cicd": "CI/CD",
  "/app/about": "About",
};

function NavGroup({ label, items }: { label: string; items: NavItem[] }) {
  return (
    <div className="nav-group">
      <span className="nav-group-label">{label}</span>
      <div className="nav-group-links">
        {items.map(({ label: itemLabel, to, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              isActive ? "nav-link active" : "nav-link"
            }
          >
            <Icon size={17} strokeWidth={1.9} aria-hidden="true" />
            <span>{itemLabel}</span>
          </NavLink>
        ))}
      </div>
    </div>
  );
}

export function AppShell() {
  const auth = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const currentLabel = routeLabels[location.pathname] ?? "Workspace";

  async function signOut() {
    await auth.logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <ShieldCheck size={21} strokeWidth={2} />
          </div>
          <div className="brand-copy">
            <strong>BuildShield-CI</strong>
            <span>Supply-chain security</span>
          </div>
        </div>

        <nav className="navigation" aria-label="Primary navigation">
          <NavGroup label="Security workspace" items={analysisNav} />
          <NavGroup label="Operations" items={operationsNav} />
        </nav>

        <div className="sidebar-footer">
          <div className="session-chip">
            <span className="status-dot" aria-hidden="true" />
            <div>
              <strong>{auth.username ?? "Administrator"}</strong>
              <span>Secure session</span>
            </div>
          </div>

          <button
            className="ghost-button"
            type="button"
            onClick={() => void signOut()}
          >
            <LogOut size={16} aria-hidden="true" />
            Sign out
          </button>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div className="topbar-context" aria-label="Current location">
            <span className="topbar-product">BuildShield-CI</span>
            <span className="topbar-separator" aria-hidden="true">
              /
            </span>
            <span>{currentLabel}</span>
          </div>

          <div className="health-pill">
            <ShieldCheck size={15} strokeWidth={2} aria-hidden="true" />
            Protected workspace
          </div>
        </header>

        <main className="workspace-content">
          <Outlet />
        </main>
      </section>
    </div>
  );
}
