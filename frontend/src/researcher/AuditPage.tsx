import { admin } from "../api";
import { Alert, Card, Table } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";

interface Row { id: number; timestamp: string; actor: string; action: string; entity_type: string | null; entity_id: string | null; details: Record<string, unknown> | null }

export default function AuditPage() {
  const { data, error } = useLoad(() => admin<Row[]>("GET", "/audit?limit=500"));
  return (
    <>
      <PageTitle title="Audit log" subtitle="Configuration changes, locks, imports, exports, contact access, exclusions and deletions. Contains no email addresses." />
      {error && <Alert kind="error">{error}</Alert>}
      <Card>
        <Table head={["Time", "Actor", "Action", "Entity", "Details"]}
          rows={(data ?? []).map((r) => [fmtDate(r.timestamp), r.actor, <span className="font-mono text-xs">{r.action}</span>,
            r.entity_type ? `${r.entity_type} ${r.entity_id ?? ""}` : "—",
            <span className="block max-w-xl whitespace-normal font-mono text-xs">{r.details && Object.keys(r.details).length ? JSON.stringify(r.details) : ""}</span>])} />
      </Card>
    </>
  );
}
