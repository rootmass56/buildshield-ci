import {
  lazy,
  Suspense,
} from "react";
import {
  Navigate,
  Outlet,
  Route,
  Routes,
} from "react-router-dom";

import { useAuth } from "./auth/AuthContext";
import { LoadingScreen } from "./components/LoadingScreen";
import { AppShell } from "./layouts/AppShell";
import { LoginPage } from "./pages/LoginPage";

const OverviewPage = lazy(() =>
  import("./pages/OverviewPage").then((module) => ({
    default: module.OverviewPage,
  })),
);

const ScannerPage = lazy(() =>
  import("./pages/ScannerPage").then((module) => ({
    default: module.ScannerPage,
  })),
);

const FindingsPage = lazy(() =>
  import("./pages/FindingsPage").then((module) => ({
    default: module.FindingsPage,
  })),
);

const PolicyPage = lazy(() =>
  import("./pages/PolicyPage").then((module) => ({
    default: module.PolicyPage,
  })),
);

const InventoryPage = lazy(() =>
  import("./pages/InventoryPage").then((module) => ({
    default: module.InventoryPage,
  })),
);

const VulnerabilityIntelPage = lazy(() =>
  import("./pages/VulnerabilityIntelPage").then((module) => ({
    default: module.VulnerabilityIntelPage,
  })),
);

const ComparePage = lazy(() =>
  import("./pages/ComparePage").then((module) => ({
    default: module.ComparePage,
  })),
);

const HistoryPage = lazy(() =>
  import("./pages/HistoryPage").then((module) => ({
    default: module.HistoryPage,
  })),
);

const ReportsPage = lazy(() =>
  import("./pages/ReportsPage").then((module) => ({
    default: module.ReportsPage,
  })),
);

const CicdPage = lazy(() =>
  import("./pages/CicdPage").then((module) => ({
    default: module.CicdPage,
  })),
);

const AboutPage = lazy(() =>
  import("./pages/AboutPage").then((module) => ({
    default: module.AboutPage,
  })),
);

function RequireAuthentication() {
  const auth = useAuth();

  if (!auth.ready) {
    return <LoadingScreen />;
  }

  if (!auth.authenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}

function RootRedirect() {
  const auth = useAuth();

  if (!auth.ready) {
    return <LoadingScreen />;
  }

  return (
    <Navigate
      to={auth.authenticated ? "/app" : "/login"}
      replace
    />
  );
}

export default function App() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <Routes>
        <Route path="/" element={<RootRedirect />} />
        <Route path="/login" element={<LoginPage />} />

        <Route element={<RequireAuthentication />}>
          <Route path="/app" element={<AppShell />}>
            <Route index element={<OverviewPage />} />
            <Route path="scanner" element={<ScannerPage />} />
            <Route path="findings" element={<FindingsPage />} />
            <Route path="policy" element={<PolicyPage />} />
            <Route path="inventory" element={<InventoryPage />} />
            <Route
              path="vulnerability-intelligence"
              element={<VulnerabilityIntelPage />}
            />
            <Route path="compare" element={<ComparePage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="cicd" element={<CicdPage />} />
            <Route path="about" element={<AboutPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
