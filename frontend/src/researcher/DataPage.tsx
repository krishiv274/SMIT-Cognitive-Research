import { useRef, useState, type DragEvent } from "react";
import { Link } from "react-router-dom";
import { admin, adminDownload, getAdminToken, request } from "../api";
import { Alert, Badge, Button, Card, Table, cx } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";

interface Issue { sheet: string; row: number | null; column: string | null; message: string; value?: string | null }
interface Report { ok: boolean; format: string; kind: string; files: string[]; n_errors: number; n_warnings: number; errors: Issue[]; warnings: Issue[]; missing_values: Record<string, Record<string, number>>; counts: Record<string, number>; preview: Record<string, Record<string, unknown>[]>; derived_summary: Record<string, unknown>[]; truncated: boolean }
interface Batch { id: number; file_names: string; status: string; import_kind: string; file_format: string; created_at: string; committed_at: string | null; report: Report; n_participants: number; n_trials: number; n_errors?: number; n_warnings?: number; analysis?: { analysis_run_id?: number; error?: string } }

const TEMPLATES = [
  ["SMIT_Data_Collection_Template.xlsx", "Full workbook (recommended)"],
  ["Participant_Summary_Template.xlsx", "Summary-only workbook (reduced analyses)"],
  ["Participant_Template.csv", "Participants CSV"],
  ["Session_Template.csv", "Sessions CSV"],
  ["Trial_Data_Template.csv", "Trials CSV"],
  ["Contacts_Template_CONFIDENTIAL.csv", "Contacts CSV (confidential)"],
  ["Participant_Summary_Template.csv", "Summary-only CSV"],
];

export default function DataPage() {
  const history = useLoad(() => admin<Batch[]>("GET", "/import"));
  const [batch, setBatch] = useState<Batch | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const upload = async (files: FileList | File[]) => {
    const list = Array.from(files);
    if (!list.length) return;
    setBusy(true); setErr(null); setDone(null); setBatch(null);
    const fd = new FormData();
    list.forEach((f) => fd.append("files", f, f.name));
    try {
      const b = await request<Batch>("POST", "/api/admin/import/validate", fd, { Authorization: `Bearer ${getAdminToken()}` });
      setBatch(b);
      history.reload();
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  const onDrop = (e: DragEvent) => { e.preventDefault(); setDrag(false); void upload(e.dataTransfer.files); };
  const commit = async () => {
    if (!batch) return;
    setBusy(true);
    try {
      const r = await request<Batch & { committed: Record<string, number> }>("POST", `/api/admin/import/${batch.id}/commit`, undefined, { Authorization: `Bearer ${getAdminToken()}` });
      setDone(`Imported ${r.committed.participants} participants, ${r.committed.sessions} sessions and ${r.committed.trials} trials. ` +
        (r.analysis?.analysis_run_id ? `Analysis run #${r.analysis.analysis_run_id} completed automatically.` : r.analysis?.error ?? ""));
      setBatch(null); history.reload();
    } catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  const cancel = async () => {
    if (!batch) return;
    await request("POST", `/api/admin/import/${batch.id}/cancel`, undefined, { Authorization: `Bearer ${getAdminToken()}` });
    setBatch(null); history.reload();
  };
  const rep = batch?.report;

  return (
    <>
      <PageTitle title="Import / Export" subtitle="Upload genuine data collected outside the app, or export the de-identified dataset. Both routes feed the same analysis pipeline." />
      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Upload data" className="lg:col-span-2">
          <div onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)} onDrop={onDrop}
            className={cx("flex flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center", drag ? "border-blue-600 bg-blue-50 dark:bg-blue-950" : "border-slate-300 dark:border-slate-700")}>
            <p className="font-semibold">Drag & drop the completed workbook here</p>
            <p className="mt-1 text-sm text-slate-500">.xlsx workbook, or several .csv files together (participants + sessions + trials), or a SMIT .json export. Max 15 MB.</p>
            <input ref={input} type="file" multiple accept=".xlsx,.csv,.json" className="hidden" data-testid="file-input" onChange={(e) => e.target.files && upload(e.target.files)} />
            <Button className="mt-4" variant="secondary" disabled={busy} onClick={() => input.current?.click()}>{busy ? "Validating…" : "Choose files"}</Button>
          </div>
          {err && <div className="mt-4"><Alert kind="error">{err}</Alert></div>}
          {done && <div className="mt-4"><Alert kind="success">{done} <Link className="underline" to="/researcher/analysis">View analysis →</Link></Alert></div>}
        </Card>
        <Card title="Templates & export">
          <ul className="space-y-1 text-sm">
            {TEMPLATES.map(([f, l]) => <li key={f}><button className="text-left text-blue-700 underline dark:text-blue-400" onClick={() => adminDownload(`/templates/${f}`, f)}>{l}</button></li>)}
          </ul>
          <h3 className="mt-5 font-semibold">De-identified export (main study)</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {(["xlsx", "csv", "json"] as const).map((f) => <Button key={f} variant="secondary" onClick={() => adminDownload(`/export?fmt=${f}&scope=main`, `export.${f}`)}>.{f}</Button>)}
          </div>
          <p className="mt-2 text-xs text-slate-500">Exports never contain email addresses.</p>
        </Card>
      </div>

      {rep && batch && (
        <Card title={<>Validation preview — {batch.file_names}</>} className="mt-6"
          actions={<div className="flex gap-2">
            <Button disabled={!rep.ok || busy} onClick={commit}>Confirm import</Button>
            <Button variant="secondary" onClick={cancel}>Cancel</Button>
          </div>}>
          {rep.ok ? <Alert kind="success">Validation passed ({rep.kind} import, {rep.format}). Review the preview and warnings, then confirm. Data are committed in a single transaction.</Alert>
            : <Alert kind="error">Validation failed with {rep.n_errors} error(s){rep.truncated ? " (list truncated)" : ""}. Nothing has been imported. Correct the file and upload it again — values are never corrected silently.</Alert>}
          <div className="mt-4 flex flex-wrap gap-2 text-sm">{Object.entries(rep.counts).map(([k, v]) => <Badge key={k} tone="blue">{k}: {v}</Badge>)}</div>
          {rep.errors.length > 0 && <><h3 className="mt-5 font-semibold text-red-700 dark:text-red-400">Errors</h3><IssueTable issues={rep.errors} /></>}
          {rep.warnings.length > 0 && <><h3 className="mt-5 font-semibold text-amber-700 dark:text-amber-400">Warnings</h3><IssueTable issues={rep.warnings} /></>}
          {Object.keys(rep.missing_values).length > 0 && (
            <><h3 className="mt-5 font-semibold">Missing values (blank cells)</h3>
              <div className="mt-2 text-sm">{Object.entries(rep.missing_values).map(([s, m]) => <p key={s}><strong>{s}:</strong> {Object.entries(m).map(([c, n]) => `${c} ${n}`).join(", ") || "none"}</p>)}</div></>
          )}
          {rep.derived_summary.length > 0 && (
            <><h3 className="mt-5 font-semibold">Recalculated accuracy per participant (from raw trials)</h3>
              <Table head={Object.keys(rep.derived_summary[0])} rows={rep.derived_summary.slice(0, 30).map((r) => Object.values(r).map((v) => typeof v === "number" ? v.toFixed(3) : String(v ?? "—")))} /></>
          )}
          {Object.entries(rep.preview).map(([sheet, rows]) => rows.length > 0 && (
            <div key={sheet}><h3 className="mt-5 font-semibold">{sheet} (first {rows.length} rows)</h3>
              <Table head={Object.keys(rows[0])} rows={rows.map((r) => Object.values(r).map((v) => String(v ?? "")))} /></div>
          ))}
        </Card>
      )}

      <Card title="Import history (audit)" className="mt-6">
        <Table head={["#", "Files", "Kind", "Status", "Participants", "Trials", "Errors", "Created", "Committed"]} empty="No imports yet."
          rows={(history.data ?? []).map((b) => [b.id, b.file_names, b.import_kind, <Badge tone={b.status === "committed" ? "green" : b.status === "invalid" ? "red" : "slate"}>{b.status}</Badge>,
            b.n_participants, b.n_trials, b.n_errors ?? "—", fmtDate(b.created_at), fmtDate(b.committed_at)])} />
      </Card>
    </>
  );
}

function IssueTable({ issues }: { issues: Issue[] }) {
  return <div className="mt-2 max-h-80 overflow-auto"><Table head={["Sheet", "Row", "Column", "Problem", "Value"]} rows={issues.map((i) => [i.sheet, i.row ?? "—", i.column ?? "—", <span className="whitespace-normal">{i.message}</span>, i.value ?? ""])} /></div>;
}
