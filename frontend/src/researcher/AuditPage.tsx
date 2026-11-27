import { admin } from "../api";
import { Alert, Card, Table } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";

interface Row { id: number; timestamp: string; actor: string; action: string; entity_type: string | null; entity_id: string | null; details: Record<string, unknown> | null }

export default function AuditPage() {
  const { data, error, loading } = useLoad(() => admin<Row[]>("GET", "/audit?limit=500"));
  return (
    <>
      <PageTitle title="Audit log" subtitle="Configuration changes, locks, imports, exports, contact access, exclusions and deletions. Contains no email addresses." />
      {error && <Alert kind="error">{error}</Alert>}
      <Card>
        <p className="mb-3 text-sm text-slate-500 dark:text-slate-400">{data ? `Latest ${data.length} entries, newest first. Scroll inside the table to see older entries.` : ""}</p>
        <Table maxHeight="calc(100vh - 15rem)" head={["Time", "Actor", "Action", "Entity", "Details"]} empty={loading && !data ? "Loading…" : "No audit entries yet."}
          rows={(data ?? []).map((r) => [fmtDate(r.timestamp, true), r.actor, <span className="font-mono text-xs">{r.action}</span>,
            r.entity_type ? <span title={r.entity_id ?? ""}>{r.entity_type} <span className="font-mono text-xs">{r.entity_id && r.entity_id.length > 20 ? `${r.entity_id.slice(0, 12)}…` : r.entity_id ?? ""}</span></span> : "—",
            <span className="block min-w-48 max-w-xl whitespace-normal break-words text-xs">{r.details ? Object.entries(r.details).filter(([, v]) => v !== "" && v !== null && v !== undefined).map(([k, v]) => <span key={k} className="mr-3 inline-block"><span className="text-slate-500">{k.replace(/_/g, " ")}:</span> {Array.isArray(v) ? v.map(String).join(", ") : typeof v === "object" ? JSON.stringify(v) : String(v)}</span>) : null}</span>])} />
      </Card>
    </>
  );
}
