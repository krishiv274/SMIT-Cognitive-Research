import { useEffect, useState } from "react";
import { admin } from "../api";
import { Alert, Badge, Button, Card, Field, Table, inputCls } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";

export interface ConfigRow { id: number; version_number: number; name: string; experiment_version: string; status: string; is_active_main: boolean; config: Record<string, any>; notes: string | null; lock_justification: string | null; created_at: string; locked_at: string | null; sessions_using: number; deviations_from_specification: string[] }

const FIELDS: { section: string; key: string; label: string; hint: string; step?: number; options?: string[] }[] = [
  { section: "grid", key: "highlight_count", label: "Highlighted cells (set size)", hint: "Floor/ceiling lever. Spec: 4" },
  { section: "timing", key: "fixation_ms", label: "Fixation (ms)", hint: "Spec: 500" },
  { section: "timing", key: "memory_stimulus_ms", label: "Memory stimulus exposure (ms)", hint: "Spec: 500 (consolidation window 200–500 ms)" },
  { section: "timing", key: "post_stimulus_blank_ms", label: "Post-stimulus blank (ms)", hint: "Optional consolidation gap. Default 0" },
  { section: "timing", key: "interference_ms", label: "Interference phase (ms)", hint: "Spec: 3000" },
  { section: "timing", key: "retention_ms", label: "Additional retention (ms)", hint: "Spec: 1000" },
  { section: "timing", key: "recognition_deadline_ms", label: "Response deadline (ms)", hint: "Spec: 2000" },
  { section: "timing", key: "iti_min_ms", label: "ITI minimum (ms)", hint: "Spec: 800" },
  { section: "timing", key: "iti_max_ms", label: "ITI maximum (ms)", hint: "Spec: 1200" },
  { section: "timing", key: "break_min_s", label: "Minimum break between blocks (s)", hint: "Default 20" },
  { section: "trials", key: "trials_per_condition", label: "Trials per condition", hint: "Spec: 20" },
  { section: "trials", key: "practice_per_condition", label: "Practice trials per condition", hint: "Spec: 2" },
  { section: "trials", key: "change_type", label: "Recognition difficulty (moved cell)", hint: "any / adjacent (harder) / non_adjacent (easier)", options: ["any", "adjacent", "non_adjacent"] },
];

export default function ConfigPage() {
  const { data, error, reload } = useLoad(() => admin<ConfigRow[]>("GET", "/configs"));
  const [edit, setEdit] = useState<Record<string, any> | null>(null);
  const [base, setBase] = useState<ConfigRow | null>(null);
  const [notes, setNotes] = useState("");
  const [json, setJson] = useState(false);
  const [jsonText, setJsonText] = useState("");
  const [msg, setMsg] = useState<{ kind: "error" | "success" | "warn"; text: string } | null>(null);
  const [lockRow, setLockRow] = useState<ConfigRow | null>(null);
  const [just, setJust] = useState("");

  useEffect(() => { if (edit) setJsonText(JSON.stringify(edit, null, 2)); }, [edit, json]);

  const startEdit = (r: ConfigRow) => { setBase(r); setEdit(structuredClone(r.config)); setNotes(""); setMsg(null); };
  const setVal = (sec: string, key: string, v: string, isText: boolean) => setEdit((e) => e && ({ ...e, [sec]: { ...e[sec], [key]: isText ? v : Number(v) } }));

  const save = async (asNew: boolean) => {
    if (!edit || !base) return;
    let cfg = edit;
    if (json) {
      try { cfg = JSON.parse(jsonText); } catch { setMsg({ kind: "error", text: "JSON is not valid." }); return; }
    }
    const params = (c: Record<string, any>) => JSON.stringify({ ...c, name: undefined, description: undefined });
    if (asNew && params(cfg) === params(base.config)) {
      setMsg({ kind: "warn", text: `Nothing was changed, so no new version was saved (it would duplicate ${base.experiment_version}). Change a parameter first, or use ${base.experiment_version} directly — pilot sessions can run on any version.` });
      return;
    }
    try {
      const r = asNew
        ? await admin<ConfigRow>("POST", "/configs", { config: cfg, notes, parent_id: base.id })
        : await admin<ConfigRow>("PUT", `/configs/${base.id}`, { config: cfg, notes });
      setMsg({ kind: "success", text: `Saved draft ${r.experiment_version}.` + (r.deviations_from_specification.length ? ` Deviations from specification: ${r.deviations_from_specification.join("; ")}` : "") });
      setEdit(null);
      reload();
    } catch (e) { setMsg({ kind: "error", text: e instanceof Error ? e.message : String(e) }); }
  };

  const remove = async (r: ConfigRow) => {
    const typed = window.prompt(`Permanently delete ${r.experiment_version}${r.is_active_main ? " (the ACTIVE main-study configuration — the study will close)" : ""}?\n\nThis cannot be undone. Type the version ID to confirm:`);
    if (typed === null) return;
    try {
      await admin("DELETE", `/configs/${r.id}`, { reason: "Deleted by the research team from the dashboard", confirm_version: typed.trim() });
      setMsg({ kind: "success", text: `${r.experiment_version} was permanently deleted.` });
      if (base?.id === r.id) setEdit(null);
      reload();
    } catch (e) { setMsg({ kind: "error", text: e instanceof Error ? e.message : String(e) }); }
  };

  const lock = async () => {
    if (!lockRow) return;
    try {
      const r = await admin<ConfigRow>("POST", `/configs/${lockRow.id}/lock`, { justification: just });
      setMsg({ kind: "success", text: `Locked ${r.experiment_version}. The main study is now open with this configuration.` });
      setLockRow(null); setJust(""); reload();
    } catch (e) { setMsg({ kind: "error", text: e instanceof Error ? e.message : String(e) }); }
  };

  return (
    <>
      <PageTitle title="Experiment configuration" subtitle="Edit parameters as DRAFT versions for pilot testing; lock one version for the main study. Locked versions cannot be changed silently — every change creates a new audited version." />
      {msg && <div className="mb-4"><Alert kind={msg.kind}>{msg.text}</Alert></div>}
      {error && <Alert kind="error">{error}</Alert>}
      {lockRow && (
        <Card title={`Lock ${lockRow.experiment_version} for the main study`} className="mb-6 border-amber-400">
          <Alert kind="warn">After locking, main-study sessions use exactly these parameters and record this version. Lock only after human pilot testing. {data?.some((r) => r.is_active_main) && "The currently active configuration will be retired; if main data were already collected this is a protocol deviation that must be reported."}</Alert>
          {lockRow.deviations_from_specification.length > 0 && <div className="mt-3"><Alert kind="info">Differences from the original specification (document the pilot-based justification): {lockRow.deviations_from_specification.join("; ")}</Alert></div>}
          <div className="mt-4"><Field label="Justification (required, recorded in the audit log)"><textarea className={inputCls} rows={3} value={just} onChange={(e) => setJust(e.target.value)} placeholder="e.g. Pilot with 4 volunteers: control accuracy 72–90%, secondary accuracy ≥ 88%; no changes needed." /></Field></div>
          <div className="mt-3 flex gap-2"><Button disabled={just.trim().length < 10} onClick={lock}>Lock configuration</Button><Button variant="secondary" onClick={() => setLockRow(null)}>Cancel</Button></div>
        </Card>
      )}
      {edit && base && (
        <Card title={`Editing (based on ${base.experiment_version})`} className="mb-6" actions={<Button variant="ghost" onClick={() => setJson((j) => !j)}>{json ? "Form view" : "Advanced JSON"}</Button>}>
          {json ? (
            <textarea className={inputCls + " font-mono text-xs"} rows={24} value={jsonText} onChange={(e) => setJsonText(e.target.value)} />
          ) : (
            <div className="grid gap-4 md:grid-cols-3">
              {FIELDS.map((f) => (
                <Field key={f.section + f.key} label={f.label} hint={f.hint}>
                  {f.options ? (
                    <select className={inputCls} value={edit[f.section][f.key]} onChange={(e) => setVal(f.section, f.key, e.target.value, true)}>{f.options.map((o) => <option key={o}>{o}</option>)}</select>
                  ) : (
                    <input type="number" className={inputCls} value={edit[f.section][f.key]} onChange={(e) => setVal(f.section, f.key, e.target.value, false)} />
                  )}
                </Field>
              ))}
              <Field label="Visual secondary task" hint="symmetry (default) or centre-cell judgement">
                <select className={inputCls} value={edit.secondary_tasks.visual.probe} onChange={(e) => setEdit({ ...edit, secondary_tasks: { ...edit.secondary_tasks, visual: { ...edit.secondary_tasks.visual, probe: e.target.value } } })}>
                  <option value="symmetry">symmetry</option><option value="centre">centre</option>
                </select>
              </Field>
              <Field label="Arithmetic operand range" hint="min–max operand (difficulty lever)">
                <div className="flex gap-2">
                  <input type="number" className={inputCls} value={edit.secondary_tasks.numerical.operand_min} onChange={(e) => setEdit({ ...edit, secondary_tasks: { ...edit.secondary_tasks, numerical: { ...edit.secondary_tasks.numerical, operand_min: Number(e.target.value) } } })} />
                  <input type="number" className={inputCls} value={edit.secondary_tasks.numerical.operand_max} onChange={(e) => setEdit({ ...edit, secondary_tasks: { ...edit.secondary_tasks, numerical: { ...edit.secondary_tasks.numerical, operand_max: Number(e.target.value) } } })} />
                </div>
              </Field>
              <Field label="Configuration name"><input className={inputCls} value={edit.name} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></Field>
            </div>
          )}
          <div className="mt-4"><Field label="Change notes (why?)"><input className={inputCls} value={notes} onChange={(e) => setNotes(e.target.value)} /></Field></div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={() => save(true)}>Save as new draft version</Button>
            {base.status === "draft" && base.sessions_using === 0 && <Button variant="secondary" onClick={() => save(false)}>Update this draft</Button>}
            <Button variant="ghost" onClick={() => setEdit(null)}>Cancel</Button>
          </div>
        </Card>
      )}
      <Card title="Versions">
        <Table head={["Version", "Status", "Name", "Created", "Sessions", "Deviations from spec", "Actions"]}
          rows={(data ?? []).map((r) => [
            <span className="font-mono text-xs">{r.experiment_version}</span>,
            r.is_active_main ? <Badge tone="green">locked · ACTIVE</Badge> : <Badge tone={r.status === "draft" ? "blue" : "slate"}>{r.status}</Badge>,
            <span title={r.notes ?? ""} className="block min-w-48 whitespace-normal">{r.name}</span>, fmtDate(r.created_at), r.sessions_using,
            r.deviations_from_specification.length ? <span className="text-xs">{r.deviations_from_specification.join("; ")}</span> : "none",
            <div className="flex gap-1">
              <Button variant="ghost" className="px-2 py-1" onClick={() => startEdit(r)}>{r.status === "draft" ? "Edit" : "Copy to draft"}</Button>
              {r.status === "draft" && <Button variant="ghost" className="px-2 py-1" onClick={() => setLockRow(r)}>Lock</Button>}
              {r.sessions_using === 0 && <Button variant="ghost" className="px-2 py-1 text-red-700 dark:text-red-400" onClick={() => remove(r)}>Delete</Button>}
            </div>,
          ])} />
      </Card>
    </>
  );
}
