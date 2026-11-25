import { useState } from "react";
import { admin } from "../api";
import { Alert, Badge, Button, Card, GridIllustration, Table, inputCls } from "../components/ui";
import type { PlanTrial, TrialPlan } from "../types";
import type { ConfigRow } from "./ConfigPage";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";
import SessionDetail from "./SessionDetail";

interface P { participant_id: string; sessions: { session_id: string; completion_status: string; experiment_version: string; main_trials_saved: number; n_main_planned: number; created_at: string }[] }

export default function PilotPage() {
  const configs = useLoad(() => admin<ConfigRow[]>("GET", "/configs"));
  const pilots = useLoad(() => admin<P[]>("GET", "/participants?scope=pilot"));
  const [cfgId, setCfgId] = useState<number | "">("");
  const [link, setLink] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [session, setSession] = useState<string | null>(null);
  const [plan, setPlan] = useState<TrialPlan | null>(null);

  const launch = async () => {
    setErr(null);
    try {
      const r = await admin<{ url: string; experiment_version: string }>("POST", "/pilot/launch", { config_id: cfgId || null });
      setLink(r.url);
      window.open(r.url, "_blank", "noopener");
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
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
            <select className={inputCls + " mt-1 w-80"} value={cfgId} onChange={(e) => setCfgId(e.target.value ? Number(e.target.value) : "")}>
              <option value="">Latest draft (default)</option>
              {(configs.data ?? []).map((c) => <option key={c.id} value={c.id}>{c.experiment_version} — {c.status}</option>)}
            </select>
          </label>
          <Button onClick={launch}>Start pilot session (new tab)</Button>
          <Button variant="secondary" onClick={preview}>Preview stimuli</Button>
        </div>
        {link && <p className="mt-3 text-sm">Pilot link (valid 6 h): <a className="break-all text-blue-700 underline dark:text-blue-400" href={link} target="_blank" rel="noopener">{window.location.origin}{link}</a></p>}
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
      <Card title="Pilot sessions (debugging: event timestamps, timing deviations, stimulus previews)">
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
