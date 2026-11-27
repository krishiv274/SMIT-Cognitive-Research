import { useState, type ReactNode } from "react";
import { admin } from "../api";
import { Alert, Badge, Button, Card, GridIllustration, Table } from "../components/ui";
import { fmtDate, useLoad } from "./ResearcherApp";

interface TrialRow { [k: string]: unknown; trial_id: number; trial_number: number; practice_trial: boolean; condition: string; original_pattern: string; recognition_pattern: string; correct_answer: string; participant_response: string | null; is_correct: boolean | null; reaction_time_ms: number | null; interference_stimulus: string | null; interference_response: string | null; interference_accuracy: boolean | null; timing_quality_flag: string; timing_notes: string | null; focus_loss: boolean; exclusion_status: string; event_timestamps: Record<string, number> | null }
interface Detail { session: Record<string, unknown>; min_valid_rt_ms?: number; trials: TrialRow[]; timing_summary: Record<string, { n: number; mean_deviation_ms: number; max_abs_deviation_ms: number; median_deviation_ms: number }>; flags: Record<string, number> }

/** Column header with an explanation on hover (dotted underline marks it). */
function H({ t, children }: { t: string; children: ReactNode }) {
  return <span title={t} className="cursor-help underline decoration-dotted underline-offset-2">{children}</span>;
}

const pat = (s: string) => s.split("-").filter(Boolean).map(Number);
// Round first so tiny negatives (e.g. -0.02) show as "0.0", not "-0.0".
const f1 = (x: unknown) => (typeof x === "number" && isFinite(x) ? (Math.round(x * 10) / 10 + 0).toFixed(1) : "—");

export default function SessionDetail({ sessionId, onClose }: { sessionId: string; onClose: () => void }) {
  const { data, error, reload } = useLoad(() => admin<Detail>("GET", `/sessions/${sessionId}`), [sessionId]);
  const [preview, setPreview] = useState<TrialRow | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  if (error) return <Card reveal title="Session" actions={<Button variant="secondary" onClick={onClose}>Close</Button>}><Alert kind="error">{error}</Alert></Card>;
  if (!data) return <Card reveal><p className="text-sm">Loading session…</p></Card>;
  const s = data.session;
  const setStatus = async (status: "abandoned" | "incomplete") => {
    const reason = window.prompt(`Reason for marking this session as ${status}:`, status === "abandoned" ? "Participant left before finishing" : "");
    if (reason === null) return;
    if (reason.trim().length < 3) { setMsg("Please give a reason of at least 3 characters."); return; }
    try {
      setMsg(null);
      await admin("POST", `/sessions/${sessionId}/status`, { completion_status: status, reason });
      reload();
    } catch (e) { setMsg(e instanceof Error ? e.message : String(e)); }
  };
  const toggle = async (t: TrialRow) => {
    const reason = window.prompt(t.exclusion_status === "excluded" ? "Reason for re-including this trial:" : "Documented reason for excluding this trial:");
    if (reason === null) return;
    if (reason.trim().length < 3) { setMsg("Please give a reason of at least 3 characters."); return; }
    try {
      setMsg(null);
      await admin("POST", `/trials/${t.trial_id}/exclusion`, { excluded: t.exclusion_status !== "excluded", reason });
      reload();
    } catch (e) { setMsg(e instanceof Error ? e.message : String(e)); }
  };
  return (
    <Card reveal title={<>Session <span className="font-mono text-base">{sessionId.slice(0, 12)}…</span> · {String(s.participant_id)}</>} actions={<Button variant="secondary" onClick={onClose}>Close</Button>}>
      {msg && <div className="mb-3"><Alert kind="error">{msg}</Alert></div>}
      <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm md:grid-cols-4">
        {[["Type", s.session_type], ["Status", s.completion_status], ["Order", s.condition_order], ["Version", s.experiment_version], ["Seed", s.random_seed],
          ["Refresh rate", s.estimated_refresh_rate ? `${s.estimated_refresh_rate} Hz` : "—"], ["Screen", s.screen_information], ["Practice attempts", s.practice_attempts],
          ["Interruptions", s.interruptions], ["Fullscreen exits", s.fullscreen_exits], ["Started", fmtDate(s.start_time as string)], ["Completed", fmtDate(s.completion_time as string)]]
          .map(([k, v]) => <div key={String(k)}><dt className="text-xs text-slate-500">{String(k)}</dt><dd className="font-medium break-all">{String(v ?? "—")}</dd></div>)}
      </dl>
      <p className="mt-2 text-xs text-slate-500 break-all">Browser: {String(s.browser_information ?? "—")}</p>
      {["registered", "in_progress", "incomplete"].includes(String(s.completion_status)) && (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-slate-500">This session is not finished.</span>
          <Button variant="secondary" className="px-3 py-1 text-xs" onClick={() => setStatus("abandoned")}>Mark as abandoned</Button>
        </div>
      )}
      <h3 className="mt-5 font-semibold">Timing (measured − planned, ms)</h3>
      <div className="mt-2 flex flex-wrap gap-2 text-sm">
        {Object.entries(data.flags).map(([k, v]) => <Badge key={k} tone={k === "ok" ? "green" : k === "warning" ? "amber" : "red"}>{k}: {v}</Badge>)}
      </div>
      <div className="mt-2">
        <Table head={["Phase", "n", "Mean deviation", "Median", "Max |deviation|"]}
          rows={Object.entries(data.timing_summary).map(([k, v]) => [k, v.n, f1(v.mean_deviation_ms), f1(v.median_deviation_ms), f1(v.max_abs_deviation_ms)])} />
      </div>
      {preview && (
        <div ref={(el) => el?.scrollIntoView?.({ behavior: "smooth", block: "nearest" })} className="mt-4 flex flex-wrap items-center gap-6 rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <GridIllustration pattern={pat(preview.original_pattern)} label="Memory" />
          {preview.condition === "C" && preview.interference_stimulus && <GridIllustration pattern={pat(preview.interference_stimulus)} color="#B35900" label="Visual distractor" />}
          {preview.condition === "B" && <div className="font-mono text-lg">{preview.interference_stimulus}</div>}
          <GridIllustration pattern={pat(preview.recognition_pattern)} label={`Probe (${preview.correct_answer})`} />
          <span className="text-sm font-semibold">Trial {preview.practice_trial ? "P" : ""}{preview.trial_number} · {preview.condition}</span>
          {preview.event_timestamps && <pre className="max-h-48 overflow-auto text-xs">{JSON.stringify(preview.event_timestamps, null, 1)}</pre>}
          <Button variant="ghost" onClick={() => setPreview(null)}>Hide preview</Button>
        </div>
      )}
      <SessionSummary trials={data.trials} minRt={data.min_valid_rt_ms ?? 200} />
      <h3 className="mt-5 font-semibold">Trials</h3>
      <p className="mt-1 text-xs text-slate-500">Fix / Mem / Int / Ret = measured durations (ms) of the fixation, memory-stimulus, interference and retention phases. Hover a column name for its meaning.</p>
      <div className="mt-2">
        <Table maxHeight="480px" head={[
          <H t="Trial number (P = practice)">#</H>, <H t="Condition: A = control (hold), B = numerical, C = visual">Cond</H>,
          <H t="Correct answer for the recognition probe">Answer</H>, <H t="Participant's answer (timeout = no key within the deadline)">Resp</H>,
          <H t="Recognition answer correct?">Correct</H>, <H t="Reaction time to the probe (ms)">RT</H>,
          <H t="Secondary-task stimulus (equation or orange pattern)">Secondary</H>, <H t="Secondary-task answer correct?">Sec. ok</H>,
          <H t="Measured fixation-cross duration (ms)">Fix</H>, <H t="Measured memory-stimulus duration (ms)">Mem</H>,
          <H t="Measured interference (middle) phase duration (ms)">Int</H>, <H t="Measured retention (blank) duration (ms)">Ret</H>,
          <H t="Timing quality: ok, warning (minor frame jank, trial still used) or invalid (trial dropped from analysis). Hover a badge for details.">Timing</H>,
          <H t="Keyboard focus: 'lost' if the window lost focus during the trial (trial becomes invalid)">Focus</H>,
          <H t="Manual exclusion by the researcher. Click a value to exclude or re-include a trial with a reason. Automatic rules (timeouts, invalid timing) are applied during analysis and are not shown here.">Manual status</H>, ""]}
          rows={data.trials.map((t) => [
            `${t.practice_trial ? "P" : ""}${t.trial_number}`, t.condition, t.correct_answer, t.participant_response ?? "timeout",
            t.is_correct === null ? "—" : t.is_correct ? "✔" : "✘", f1(t.reaction_time_ms),
            t.interference_stimulus ?? "—", t.interference_accuracy === null ? "—" : t.interference_accuracy ? "✔" : "✘",
            f1(t.actual_fixation_duration_ms), f1(t.measured_stimulus_duration_ms), f1(t.measured_interference_duration_ms), f1(t.measured_retention_duration_ms),
            <span title={t.timing_notes ?? ""}><Badge tone={t.timing_quality_flag === "ok" ? "green" : t.timing_quality_flag === "warning" ? "amber" : "red"}>{t.timing_quality_flag}</Badge></span>,
            t.focus_loss ? <span className="font-semibold text-red-700 dark:text-red-400">lost</span> : <span className="text-slate-500">kept</span>,
            <button onClick={() => toggle(t)} title={t.exclusion_status === "excluded" ? "Click to re-include this trial" : "Click to exclude this trial"} className={"text-xs underline " + (t.exclusion_status === "excluded" ? "text-red-700 dark:text-red-400" : "")}>{t.exclusion_status}</button>,
            <button onClick={() => setPreview(preview?.trial_id === t.trial_id ? null : t)} className="text-xs text-blue-700 underline dark:text-blue-400">{preview?.trial_id === t.trial_id ? "hide" : "preview"}</button>,
          ])} />
      </div>
    </Card>
  );
}

const COND_NAME: Record<string, string> = { A: "A · Control", B: "B · Numerical", C: "C · Visual" };
const pct = (x: number | null) => (x === null ? "—" : `${Math.round(x * 100)}%`);
const ms = (xs: number[]) => (xs.length ? Math.round(xs.reduce((a, b) => a + b, 0) / xs.length) : null);
const med = (xs: number[]) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b), m = Math.floor(s.length / 2);
  return Math.round(s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2);
};

/** Per-condition summary of the main (non-practice) trials, using the same rules as the analysis:
 *  valid = not manually excluded and timing not invalid; accuracy counts timeouts as errors;
 *  RT = correct, valid trials with RT ≥ the anticipation cut-off; secondary accuracy counts missing answers as errors. */
function SessionSummary({ trials, minRt }: { trials: TrialRow[]; minRt: number }) {
  const main = trials.filter((t) => !t.practice_trial);
  const practice = trials.filter((t) => t.practice_trial);
  if (!main.length && !practice.length) return null;
  const row = (label: ReactNode, g: TrialRow[]) => {
    const valid = g.filter((t) => t.exclusion_status !== "excluded" && t.timing_quality_flag !== "invalid");
    const correct = valid.filter((t) => t.is_correct === true);
    const timeouts = valid.filter((t) => t.participant_response === null).length;
    const rts = correct.map((t) => t.reaction_time_ms).filter((x): x is number => typeof x === "number" && x >= minRt);
    const sec = valid.filter((t) => t.interference_stimulus !== null && t.condition !== "A");
    const secOk = sec.filter((t) => t.interference_accuracy === true).length;
    const secMissing = sec.filter((t) => t.interference_response === null).length;
    const warn = g.filter((t) => t.timing_quality_flag === "warning").length;
    const inv = g.filter((t) => t.timing_quality_flag === "invalid").length;
    const focus = g.filter((t) => t.focus_loss).length;
    const excl = g.filter((t) => t.exclusion_status === "excluded").length;
    const acc = valid.length ? correct.length / valid.length : null;
    return [
      label, g.length, valid.length,
      <span className={acc !== null && acc < 0.6 ? "font-semibold text-red-700 dark:text-red-400" : ""}>{pct(acc)} <span className="text-xs text-slate-500">({correct.length}/{valid.length})</span></span>,
      timeouts || "0", rts.length ? `${ms(rts)} / ${med(rts)}` : "—",
      sec.length ? <span><span className={secOk / sec.length < 0.6 ? "font-semibold text-red-700 dark:text-red-400" : ""}>{pct(secOk / sec.length)}</span> <span className="text-xs text-slate-500">({secOk}/{sec.length})</span>{secMissing ? <span className="block text-xs font-semibold text-amber-700 dark:text-amber-400">{secMissing} not answered</span> : null}</span> : "—",
      warn || inv ? <span>{warn ? <Badge tone="amber">{warn} warn</Badge> : null} {inv ? <Badge tone="red">{inv} invalid</Badge> : null}</span> : <Badge tone="green">all ok</Badge>,
      focus ? <span className="font-semibold text-red-700 dark:text-red-400">{focus}</span> : "0",
      excl || "0",
    ];
  };
  const conds = ["A", "B", "C"].filter((c) => main.some((t) => t.condition === c));
  return (
    <>
      <h3 className="mt-5 font-semibold">Summary</h3>
      <p className="mt-1 text-xs text-slate-500">Main trials per condition, using the analysis rules: accuracy counts timeouts as errors; RT uses correct answers ≥ {minRt} ms; trials excluded by you or with invalid timing are not "valid". Red = below 60%.</p>
      <div className="mt-2">
        <Table
          head={["Condition", "Trials", "Valid", "Accuracy", "Timeouts", <span title="Mean / median reaction time of correct answers (ms)">RT mean / median</span>, "Secondary task", "Timing", <span title="Trials during which the window lost keyboard focus">Focus lost</span>, <span title="Trials you excluded manually">Excl.</span>]}
          rows={[...conds.map((c) => row(COND_NAME[c] ?? c, main.filter((t) => t.condition === c))),
            ...(practice.length ? [row(<span className="text-slate-500">Practice (all attempts)</span>, practice)] : [])]}
          footer={main.length ? row("All main trials", main) : undefined}
        />
      </div>
    </>
  );
}
