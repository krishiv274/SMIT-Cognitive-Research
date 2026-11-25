import { useState } from "react";
import { admin, adminDownload } from "../api";
import { Alert, Badge, Button, Card, Field, Table, inputCls } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";
import SessionDetail from "./SessionDetail";

interface PSession { session_id: string; completion_status: string; condition_order: string; experiment_version: string; main_trials_saved: number; n_main_planned: number | null; created_at: string; interruptions: number }
interface P { participant_id: string; participant_type: string; age: number | null; gender: string | null; academic_course: string | null; consent_status: boolean; consent_timestamp: string | null; status: string; status_reason: string | null; data_source: string; created_at: string; has_contact: boolean; summary_only: boolean; sessions: PSession[] }

const tone = (s: string) => (s === "completed" || s === "active" ? "green" : s === "withdrawn" || s === "excluded" || s === "abandoned" ? "red" : "amber") as "green" | "red" | "amber";

export default function ParticipantsPage() {
  const [scope, setScope] = useState("main");
  const { data, error, reload } = useLoad(() => admin<P[]>("GET", `/participants?scope=${scope}`), [scope]);
  const [action, setAction] = useState<{ kind: "status" | "delete"; p: P } | null>(null);
  const [contact, setContact] = useState<Record<string, string | null>>({});
  const [session, setSession] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "error" | "success"; text: string } | null>(null);

  const reveal = async (pid: string) => {
    const r = await admin<{ email: string | null }>("GET", `/participants/${pid}/contact`);
    setContact((c) => ({ ...c, [pid]: r.email }));
  };

  return (
    <>
      <PageTitle title="Participants" subtitle="Pseudonymous participants. Email addresses are hidden and every reveal/export is recorded in the audit log."
        actions={<div className="flex gap-2">
          <select className={inputCls + " w-auto"} value={scope} onChange={(e) => setScope(e.target.value)} aria-label="Scope">
            <option value="main">Main study</option><option value="pilot">Pilot</option><option value="all">All</option>
          </select>
          <Button variant="secondary" onClick={() => adminDownload(`/export?fmt=xlsx&scope=${scope}`, "export.xlsx")}>Export de-identified (.xlsx)</Button>
          <Button variant="secondary" onClick={() => window.confirm("Download the CONFIDENTIAL contact list? This action is logged.") && adminDownload("/contacts/export", "contacts.csv")}>Contacts (confidential)</Button>
        </div>} />
      {msg && <div className="mb-4"><Alert kind={msg.kind}>{msg.text}</Alert></div>}
      {error && <Alert kind="error">{error}</Alert>}
      {session && <div className="mb-6"><SessionDetail sessionId={session} onClose={() => setSession(null)} /></div>}
      {action && <ActionPanel action={action} onDone={(t) => { setAction(null); setMsg({ kind: "success", text: t }); reload(); }} onCancel={() => setAction(null)} onError={(t) => setMsg({ kind: "error", text: t })} />}
      <Card>
        <Table
          head={["ID", "Status", "Session", "Trials", "Order", "Age", "Gender", "Course", "Consent", "Source", "Contact", "Actions"]}
          empty="No participants yet. Start the participant app or import a data file."
          rows={(data ?? []).map((p) => {
            const s = p.sessions[p.sessions.length - 1];
            return [
              <span className="font-mono font-semibold">{p.participant_id}</span>,
              <span title={p.status_reason ?? ""}><Badge tone={tone(p.status)}>{p.status}</Badge></span>,
              s ? <button className="text-left" onClick={() => setSession(s.session_id)}><Badge tone={tone(s.completion_status)}>{s.completion_status}</Badge>{p.sessions.length > 1 && <span className="ml-1 text-xs">+{p.sessions.length - 1}</span>}<div className="text-xs text-blue-700 underline dark:text-blue-400">details</div></button> : p.summary_only ? <Badge tone="blue">summary only</Badge> : "—",
              s ? `${s.main_trials_saved}/${s.n_main_planned ?? "?"}` : "—",
              s?.condition_order ?? "—",
              p.age ?? "—", p.gender ?? "—", p.academic_course ?? "—",
              p.consent_status ? <span title={fmtDate(p.consent_timestamp)}>✔ yes</span> : "no",
              p.data_source,
              p.has_contact ? (contact[p.participant_id] !== undefined ? <span className="font-mono text-xs">{contact[p.participant_id]}</span> : <button className="text-xs text-blue-700 underline dark:text-blue-400" onClick={() => reveal(p.participant_id)}>reveal</button>) : "—",
              <div className="flex gap-1">
                <Button variant="ghost" className="px-2 py-1" onClick={() => setAction({ kind: "status", p })}>Status</Button>
                <Button variant="ghost" className="px-2 py-1 text-red-700" onClick={() => setAction({ kind: "delete", p })}>Delete</Button>
              </div>,
            ];
          })}
        />
      </Card>
    </>
  );
}

function ActionPanel({ action, onDone, onCancel, onError }: { action: { kind: "status" | "delete"; p: P }; onDone: (t: string) => void; onCancel: () => void; onError: (t: string) => void }) {
  const [status, setStatus] = useState(action.p.status === "active" ? "excluded" : "active");
  const [reason, setReason] = useState("");
  const [confirmId, setConfirmId] = useState("");
  const pid = action.p.participant_id;
  const submit = async () => {
    try {
      if (action.kind === "status") {
        await admin("POST", `/participants/${pid}/status`, { status, reason });
        onDone(`${pid} is now ${status}.`);
      } else {
        await admin("DELETE", `/participants/${pid}`, { reason, confirm_participant_id: confirmId });
        onDone(`${pid} and all associated data were permanently deleted.`);
      }
    } catch (e) {
      onError(e instanceof Error ? e.message : String(e));
    }
  };
  return (
    <Card title={action.kind === "status" ? `Change status of ${pid}` : `Permanently delete ${pid}`} className="mb-6 border-amber-400">
      <div className="grid gap-4 md:grid-cols-3">
        {action.kind === "status" ? (
          <Field label="New status" hint="Excluded participants are kept but removed from analysis; withdrawn = consent withdrawn.">
            <select className={inputCls} value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="active">active (include)</option><option value="excluded">excluded</option><option value="withdrawn">withdrawn</option>
            </select>
          </Field>
        ) : (
          <Field label={`Type ${pid} to confirm`} hint="Deletes demographics, contact, sessions and trials. Cannot be undone.">
            <input className={inputCls} value={confirmId} onChange={(e) => setConfirmId(e.target.value)} />
          </Field>
        )}
        <div className="md:col-span-2"><Field label="Documented reason (required)"><input className={inputCls} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. participant requested withdrawal on 2026-12-03" /></Field></div>
      </div>
      <div className="mt-4 flex gap-2">
        <Button variant={action.kind === "delete" ? "danger" : "primary"} disabled={reason.trim().length < 3 || (action.kind === "delete" && confirmId !== pid)} onClick={submit}>
          {action.kind === "delete" ? "Delete permanently" : "Save status"}
        </Button>
        <Button variant="secondary" onClick={onCancel}>Cancel</Button>
      </div>
    </Card>
  );
}
