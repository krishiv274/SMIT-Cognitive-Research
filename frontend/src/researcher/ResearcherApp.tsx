import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { admin, getAdminToken, request, setAdminToken } from "../api";
import { Alert, Button, Field, cx, inputCls } from "../components/ui";
import AnalysisPage from "./AnalysisPage";
import AuditPage from "./AuditPage";
import ConfigPage from "./ConfigPage";
import DataPage from "./DataPage";
import OverviewPage from "./OverviewPage";
import ParticipantsPage from "./ParticipantsPage";
import PilotPage from "./PilotPage";
import ReportsPage from "./ReportsPage";
import SettingsPage from "./SettingsPage";

const NAV = [
  ["overview", "Overview"],
  ["participants", "Participants"],
  ["configuration", "Configuration"],
  ["pilot", "Pilot mode"],
  ["data", "Import / Export"],
  ["analysis", "Analysis"],
  ["reports", "Reports"],
  ["settings", "Settings"],
  ["audit", "Audit log"],
] as const;

function useTheme(): [boolean, () => void] {
  const [dark, setDark] = useState(() => {
    try {
      const s = localStorage.getItem("smit_theme");
      return s ? s === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    } catch {
      return false;
    }
  });
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try { localStorage.setItem("smit_theme", dark ? "dark" : "light"); } catch { /* ignore */ }
    return () => document.documentElement.classList.remove("dark");
  }, [dark]);
  return [dark, () => setDark((d) => !d)];
}

function Login({ onLogin }: { onLogin: () => void }) {
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErr(null);
    try {
      const r = await request<{ token: string; default_password_in_use: boolean }>("POST", "/api/admin/login", { password: pw });
      setAdminToken(r.token);
      onLogin();
    } catch (e2) {
      setErr(e2 instanceof Error ? e2.message : String(e2));
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="mx-auto flex min-h-full max-w-sm flex-col justify-center px-4">
      <form onSubmit={submit} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h1 className="text-xl font-bold">Researcher login</h1>
        <p className="mt-1 text-sm text-slate-500">SMIT research dashboard</p>
        <div className="mt-5"><Field label="Password"><input type="password" className={inputCls} value={pw} onChange={(e) => setPw(e.target.value)} autoFocus /></Field></div>
        {err && <div className="mt-3"><Alert kind="error">{err}</Alert></div>}
        <Button className="mt-5 w-full" disabled={busy || !pw}>{busy ? "Signing in…" : "Sign in"}</Button>
      </form>
    </main>
  );
}

export default function ResearcherApp() {
  const [authed, setAuthed] = useState(!!getAdminToken());
  const [dark, toggle] = useTheme();
  const [defaultPw, setDefaultPw] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const out = () => setAuthed(false);
    window.addEventListener("smit-logout", out);
    return () => window.removeEventListener("smit-logout", out);
  }, []);
  useEffect(() => {
    if (authed) admin<{ default_password_in_use: boolean }>("GET", "/overview").then((o) => setDefaultPw(o.default_password_in_use)).catch(() => undefined);
  }, [authed]);

  if (!authed) return <Login onLogin={() => setAuthed(true)} />;
  return (
    <div className="flex min-h-full flex-col md:flex-row">
      <aside className="border-b border-slate-200 bg-white md:w-56 md:shrink-0 md:border-b-0 md:border-r dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between px-4 py-4">
          <div>
            <div className="text-lg font-bold">SMIT</div>
            <div className="text-xs text-slate-500">Research dashboard</div>
          </div>
          <button className="rounded p-2 md:hidden" onClick={() => setMenuOpen((m) => !m)} aria-label="Toggle menu">☰</button>
        </div>
        <nav className={cx("flex-col gap-1 px-2 pb-4", menuOpen ? "flex" : "hidden md:flex")}>
          {NAV.map(([path, label]) => (
            <NavLink key={path} to={`/researcher/${path}`} onClick={() => setMenuOpen(false)}
              className={({ isActive }) => cx("rounded-lg px-3 py-2 text-sm font-medium", isActive ? "bg-blue-700 text-white" : "text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800")}>
              {label}
            </NavLink>
          ))}
          <div className="mt-4 flex flex-col gap-1 border-t border-slate-200 pt-3 dark:border-slate-800">
            <button className="rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800" onClick={toggle}>{dark ? "☀ Light mode" : "☾ Dark mode"}</button>
            <button className="rounded-lg px-3 py-2 text-left text-sm hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => { setAdminToken(null); setAuthed(false); }}>Sign out</button>
          </div>
        </nav>
      </aside>
      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">
        {defaultPw && <div className="mb-4"><Alert kind="warn"><strong>Security:</strong> the default researcher password is in use. Set <code>SMIT_ADMIN_PASSWORD</code> (and <code>SMIT_SECRET_KEY</code>) in <code>.env</code> before collecting real data.</Alert></div>}
        <Routes>
          <Route index element={<Navigate to="overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="participants" element={<ParticipantsPage />} />
          <Route path="configuration" element={<ConfigPage />} />
          <Route path="pilot" element={<PilotPage />} />
          <Route path="data" element={<DataPage />} />
          <Route path="analysis" element={<AnalysisPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="*" element={<Navigate to="overview" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export function PageTitle({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}

export function useLoad<T>(fn: () => Promise<T>, deps: unknown[] = []): { data: T | null; error: string | null; loading: boolean; reload: () => void } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [n, setN] = useState(0);
  useEffect(() => {
    let alive = true;
    setLoading(true);
    fn().then((d) => { if (alive) { setData(d); setError(null); } })
      .catch((e) => alive && setError(e instanceof Error ? e.message : String(e)))
      .finally(() => alive && setLoading(false));
    return () => { alive = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, n]);
  return { data, error, loading, reload: () => setN((x) => x + 1) };
}

export function fmtDate(s: string | null | undefined): string {
  if (!s) return "—";
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toLocaleString();
}
