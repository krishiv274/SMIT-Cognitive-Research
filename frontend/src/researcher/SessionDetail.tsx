import { useState } from "react";
import { admin } from "../api";
import { Alert, Badge, Button, Card, GridIllustration, Table } from "../components/ui";
import { fmtDate, useLoad } from "./ResearcherApp";

interface TrialRow { [k: string]: unknown; trial_id: number; trial_number: number; practice_trial: boolean; condition: string; original_pattern: string; recognition_pattern: string; correct_answer: string; participant_response: string | null; is_correct: boolean | null; reaction_time_ms: number | null; interference_stimulus: string | null; interference_response: string | null; interference_accuracy: boolean | null; timing_quality_flag: string; timing_notes: string | null; focus_loss: boolean; exclusion_status: string; event_timestamps: Record<string, number> | null }
interface Detail { session: Record<string, unknown>; trials: TrialRow[]; timing_summary: Record<string, { n: number; mean_deviation_ms: number; max_abs_deviation_ms: number; median_deviation_ms: number }>; flags: Record<string, number> }

const pat = (s: string) => s.split("-").filter(Boolean).map(Number);
const f1 = (x: unknown) => (typeof x === "number" ? x.toFixed(1) : "—");

export default function SessionDetail({ sessionId, onClose }: { sessionId: string; onClose: () => void }) {
  const { data, error, reload } = useLoad(() => admin<Detail>("GET", `/sessions/${sessionId}`), [sessionId]);
  const [preview, setPreview] = useState<TrialRow | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  if (error) return <Alert kind="error">{error}</Alert>;
  if (!data) return <p>Loading session…</p>;
  const s = data.session;
  const toggle = async (t: TrialRow) => {
    const reason = window.prompt(t.exclusion_status === "excluded" ? "Reason for re-including this trial:" : "Documented reason for excluding this trial:");
    if (!reason || reason.trim().length < 3) return;
    try {
      await admin("POST", `/trials/${t.trial_id}/exclusion`, { excluded: t.exclusion_status !== "excluded", reason });
      reload();
    } catch (e) { setMsg(e instanceof Error ? e.message : String(e)); }
  };
  return (
    <Card title={<>Session <span className="font-mono text-base">{sessionId.slice(0, 12)}…</span> · {String(s.participant_id)}</>} actions={<Button variant="secondary" onClick={onClose}>Close</Button>}>
      {msg && <Alert kind="error">{msg}</Alert>}
      <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm md:grid-cols-4">
        {[["Type", s.session_type], ["Status", s.completion_status], ["Order", s.condition_order], ["Version", s.experiment_version], ["Seed", s.random_seed],
          ["Refresh rate", s.estimated_refresh_rate ? `${s.estimated_refresh_rate} Hz` : "—"], ["Screen", s.screen_information], ["Practice attempts", s.practice_attempts],
          ["Interruptions", s.interruptions], ["Fullscreen exits", s.fullscreen_exits], ["Started", fmtDate(s.start_time as string)], ["Completed", fmtDate(s.completion_time as string)]]
          .map(([k, v]) => <div key={String(k)}><dt className="text-xs text-slate-500">{String(k)}</dt><dd className="font-medium break-all">{String(v ?? "—")}</dd></div>)}
      </dl>
      <p className="mt-2 text-xs text-slate-500 break-all">Browser: {String(s.browser_information ?? "—")}</p>
      <h3 className="mt-5 font-semibold">Timing (measured − planned, ms)</h3>
      <div className="mt-2 flex flex-wrap gap-2 text-sm">
        {Object.entries(data.flags).map(([k, v]) => <Badge key={k} tone={k === "ok" ? "green" : k === "warning" ? "amber" : "red"}>{k}: {v}</Badge>)}
      </div>
      <div className="mt-2">
        <Table head={["Phase", "n", "Mean deviation", "Median", "Max |deviation|"]}
          rows={Object.entries(data.timing_summary).map(([k, v]) => [k, v.n, f1(v.mean_deviation_ms), f1(v.median_deviation_ms), f1(v.max_abs_deviation_ms)])} />
      </div>
      {preview && (
        <div className="mt-4 flex flex-wrap items-center gap-6 rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <GridIllustration pattern={pat(preview.original_pattern)} label="Memory" />
          {preview.condition === "C" && preview.interference_stimulus && <GridIllustration pattern={pat(preview.interference_stimulus)} color="#B35900" label="Visual distractor" />}
          {preview.condition === "B" && <div className="font-mono text-lg">{preview.interference_stimulus}</div>}
          <GridIllustration pattern={pat(preview.recognition_pattern)} label={`Probe (${preview.correct_answer})`} />
          {preview.event_timestamps && <pre className="text-xs">{JSON.stringify(preview.event_timestamps, null, 1)}</pre>}
          <Button variant="ghost" onClick={() => setPreview(null)}>Hide preview</Button>
        </div>
      )}
      <h3 className="mt-5 font-semibold">Trials</h3>
      <div className="mt-2 max-h-[480px] overflow-auto">
        <Table head={["#", "Cond", "Answer", "Resp", "Correct", "RT", "Secondary", "Sec. ok", "Fix", "Mem", "Int", "Ret", "Timing", "Focus", "Status", ""]}
          rows={data.trials.map((t) => [
            `${t.practice_trial ? "P" : ""}${t.trial_number}`, t.condition, t.correct_answer, t.participant_response ?? "timeout",
            t.is_correct === null ? "—" : t.is_correct ? "✔" : "✘", f1(t.reaction_time_ms),
            t.interference_stimulus ?? "—", t.interference_accuracy === null ? "—" : t.interference_accuracy ? "✔" : "✘",
            f1(t.actual_fixation_duration_ms), f1(t.measured_stimulus_duration_ms), f1(t.measured_interference_duration_ms), f1(t.measured_retention_duration_ms),
            <span title={t.timing_notes ?? ""}><Badge tone={t.timing_quality_flag === "ok" ? "green" : t.timing_quality_flag === "warning" ? "amber" : "red"}>{t.timing_quality_flag}</Badge></span>,
            t.focus_loss ? "lost" : "",
            <button onClick={() => toggle(t)} className="text-xs underline">{t.exclusion_status}</button>,
            <button onClick={() => setPreview(t)} className="text-xs text-blue-700 underline dark:text-blue-400">preview</button>,
          ])} />
      </div>
    </Card>
  );
}
