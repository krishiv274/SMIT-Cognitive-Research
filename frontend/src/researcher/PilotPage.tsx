import { useEffect, useState } from "react";
import { admin } from "../api";
import { Alert, Badge, Button, Card, GridIllustration, Table, inputCls } from "../components/ui";
import type { PlanTrial, TrialPlan } from "../types";
import type { ConfigRow } from "./ConfigPage";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";
import SessionDetail from "./SessionDetail";

interface P { participant_id: string; sessions: { session_id: string; completion_status: string; experiment_version: string; main_trials_saved: number; n_main_planned: number; created_at: string }[] }

/** Pilot links are kept in this browser (they are valid for 6 hours) so they survive a page refresh. */
interface PilotLink { path: string; version: string; created: number; expires: number }
const LINKS_KEY = "smit_pilot_links";
const LINK_TTL_MS = 6 * 3600 * 1000;

function loadLinks(): PilotLink[] {
  try {
    const all = JSON.parse(localStorage.getItem(LINKS_KEY) || "[]") as PilotLink[];
    return all.filter((l) => l.expires > Date.now());
  } catch {
    return [];
  }
}

function saveLinks(links: PilotLink[]): void {
  try { localStorage.setItem(LINKS_KEY, JSON.stringify(links.slice(0, 5))); } catch { /* storage unavailable */ }
}

export default function PilotPage() {
  const configs = useLoad(() => admin<ConfigRow[]>("GET", "/configs"));
  const pilots = useLoad(() => admin<P[]>("GET", "/participants?scope=pilot"));
  const [cfgId, setCfgId] = useState<number | "">("");
  const [links, setLinks] = useState<PilotLink[]>(loadLinks);
  const [copied, setCopied] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [session, setSession] = useState<string | null>(null);
  const [plan, setPlan] = useState<TrialPlan | null>(null);

  // Refresh the pilot-session list when the researcher returns to this tab (e.g. after a pilot finished).
  useEffect(() => {
    const onFocus = () => pilots.reload();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  });

  const launch = async () => {
    setErr(null);
    // Open the tab synchronously inside the click, otherwise browsers treat it as a blocked popup.
    let tab: Window | null = null;
    try { tab = window.open("about:blank", "_blank"); } catch { tab = null; }
    try {
      const r = await admin<{ url: string; experiment_version: string }>("POST", "/pilot/launch", { config_id: cfgId || null });
      const now = Date.now();
      const next = [{ path: r.url, version: r.experiment_version, created: now, expires: now + LINK_TTL_MS }, ...loadLinks()];
      saveLinks(next);
      setLinks(next.slice(0, 5));
      let opened = false;
      if (tab) {
        try { tab.opener = null; tab.location.href = r.url; opened = true; } catch { opened = false; }
      }
      if (!opened) setErr("Your browser blocked the new tab. Use the Open button next to the link below.");
    } catch (e) {
      try { tab?.close(); } catch { /* ignore */ }
      setErr(e instanceof Error ? e.message : String(e));
    }
  };
  const copy = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(url);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      window.prompt("Copy this pilot link:", url);
    }
  };
  const revokeAll = async () => {
    if (!window.confirm("Revoke ALL pilot links? Every pilot link created so far (including links you sent to volunteers) will stop working. Pilot sessions already started are not affected.")) return;
    try {
      await admin("POST", "/pilot/revoke-all");
      saveLinks([]);
      setLinks([]);
      setErr(null);
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
  };
  const forget = (path: string) => {
    const next = loadLinks().filter((l) => l.path !== path);
    saveLinks(next);
    setLinks(next);
  };
  const preview = async () => {
    const id = cfgId || configs.data?.[0]?.id;
    if (!id) return;
    const r = await admin<{ plan: TrialPlan }>("GET", `/configs/${id}/preview?seed=${Math.floor(Math.random() * 1e6)}&order=ABC`);
    setPlan(r.plan);
  };

  return (
    <>
      <PageTitle title="Pilot mode" subtitle="Run pilot sessions with any configuration version. Pilot data are stored separately (session_type = pilot) and never enter the main analysis." />
      <Card title="Start a pilot session" className="mb-6">
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-sm">Configuration
            <select className={inputCls.replace("w-full", "") + " mt-1 block w-full sm:w-80"} value={cfgId} onChange={(e) => setCfgId(e.target.value ? Number(e.target.value) : "")}>
              <option value="">Latest draft (default)</option>
              {(configs.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.experiment_version} — {c.status}</option>)}
            </select>
          </label>
          <Button onClick={launch}>Start pilot session (new tab)</Button>
          <Button variant="secondary" onClick={preview}>Preview stimuli</Button>
          <Button variant="ghost" className="text-red-700 dark:text-red-400" onClick={revokeAll}>Revoke all pilot links</Button>
        </div>
        {links.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-sm font-semibold">Pilot links (each valid for 6 hours; can be sent to a pilot volunteer)</p>
            {links.map((l) => {
              const url = `${window.location.origin}${l.path}`;
              const mins = Math.max(0, Math.round((l.expires - Date.now()) / 60000));
              return (
                <div key={l.path} className="rounded-lg border border-slate-200 p-3 text-sm dark:border-slate-700">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs text-slate-500">{l.version} · created {new Date(l.created).toLocaleTimeString()} · expires in {Math.floor(mins / 60)} h {mins % 60} min</span>
                    <span className="flex gap-2">
                      <a className="rounded-lg border border-slate-300 px-3 py-1 text-xs font-semibold hover:bg-slate-100 dark:border-slate-700 dark:hover:bg-slate-800" href={url} target="_blank" rel="noopener noreferrer">Open</a>
                      <Button variant="secondary" className="px-3 py-1 text-xs" onClick={() => copy(url)}>{copied === url ? "Copied ✓" : "Copy link"}</Button>
                      <Button variant="ghost" className="px-3 py-1 text-xs" onClick={() => forget(l.path)}>Remove</Button>
                    </span>
                  </div>
                  <code className="mt-1 block break-all text-xs text-blue-700 dark:text-blue-400">{url}</code>
                </div>
              );
            })}
          </div>
        )}
        {err && <div className="mt-3"><Alert kind="error">{err}</Alert></div>}
        <p className="mt-3 text-xs text-slate-500">Follow experiment/documentation/Pilot_Testing_Protocol.md and record observations in Settings → Pilot observations. Automated software tests are not human pilot testing.</p>
      </Card>
      {plan && (
        <Card title="Stimulus preview (randomly generated example plan — not participant data)" className="mb-6" actions={<Button variant="ghost" onClick={() => setPlan(null)}>Close</Button>}>
          <div className="grid gap-4 md:grid-cols-3">
            {plan.blocks.map((b) => <PreviewTrial key={b.condition} t={b.trials[0]} />)}
          </div>
        </Card>
      )}
      {session && <div className="mb-6"><SessionDetail sessionId={session} onClose={() => setSession(null)} /></div>}
      <Card title="Pilot sessions (debugging: event timestamps, timing deviations, stimulus previews)" actions={<Button variant="secondary" onClick={pilots.reload}>Refresh</Button>}>
        <Table head={["Pilot ID", "Session", "Version", "Trials", "Created", ""]} empty="No pilot sessions yet."
          rows={(pilots.data ?? []).flatMap((p) => p.sessions.map((s) => [
            <span className="font-mono">{p.participant_id}</span>, <Badge tone={s.completion_status === "completed" ? "green" : "amber"}>{s.completion_status}</Badge>,
            <span className="font-mono text-xs">{s.experiment_version}</span>, `${s.main_trials_saved}/${s.n_main_planned}`, fmtDate(s.created_at),
            <Button variant="ghost" className="px-2 py-1" onClick={() => setSession(s.session_id)}>Inspect</Button>,
          ]))} />
      </Card>
    </>
  );
}

function PreviewTrial({ t }: { t: PlanTrial }) {
  return (
    <div className="rounded-lg border border-slate-200 p-3 dark:border-slate-700">
      <div className="mb-2 text-sm font-semibold">Condition {t.condition} · {t.trial_type}</div>
      <div className="flex flex-wrap items-center gap-3">
        <GridIllustration pattern={t.original_pattern} label="Memory" cell={22} />
        {t.condition === "B" && <span className="font-mono">{t.interference?.text}</span>}
        {t.condition === "C" && <GridIllustration pattern={t.interference?.pattern ?? []} color="#B35900" label={`Distractor (${t.interference?.correct})`} cell={22} />}
        {t.condition === "A" && <span className="text-xs text-slate-500">blank hold</span>}
        <GridIllustration pattern={t.recognition_pattern} label="Probe" cell={22} />
      </div>
    </div>
  );
}
