import { useState } from "react";
import { admin, adminDownload } from "../api";
import { Alert, Badge, Button, Card, Table } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";

interface Rep { id: number; created_at: string; kind: string; analysis_run_id: number | null; files: { name: string; label: string }[] }

export default function ReportsPage() {
  const list = useLoad(() => admin<Rep[]>("GET", "/reports"));
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ kind: "success" | "error" | "warn"; text: string } | null>(null);

  const gen = async (what: "report" | "presentation") => {
    setBusy(what); setMsg(null);
    try {
      const r = await admin<Rep & { message: string }>("POST", what === "report" ? "/reports/generate" : "/reports/presentation");
      setMsg({ kind: r.kind === "final" ? "success" : "warn", text: r.message });
      list.reload();
    } catch (e) { setMsg({ kind: "error", text: e instanceof Error ? e.message : String(e) }); }
    finally { setBusy(null); }
  };

  return (
    <>
      <PageTitle title="Reports & presentation" subtitle="Generates the academic report (PDF, DOCX, HTML), the statistical results workbook and the slide deck from the latest analysis run." />
      <div className="grid gap-6 md:grid-cols-2">
        <Card title="Generate Research Report">
          <p className="text-sm">Uses the most recent analysis run (run the analysis first if data changed). If no eligible genuine data exist, a <strong>preliminary protocol report</strong> is produced with results, discussion and conclusions marked as pending.</p>
          <Button className="mt-4" onClick={() => gen("report")} disabled={!!busy}>{busy === "report" ? "Generating…" : "Generate Research Report"}</Button>
        </Card>
        <Card title="Regenerate presentation">
          <p className="text-sm">Rebuilds <code>SMIT_Presentation.pptx</code>; data-dependent slides (results, discussion, conclusion) are filled from the latest analysis run or marked as pending.</p>
          <Button className="mt-4" variant="secondary" onClick={() => gen("presentation")} disabled={!!busy}>{busy === "presentation" ? "Generating…" : "Regenerate presentation"}</Button>
        </Card>
      </div>
      {msg && <div className="mt-4"><Alert kind={msg.kind}>{msg.text}</Alert></div>}
      <div className="mt-6"><Alert kind="info">Automatically generated interpretations must be reviewed and approved by the research team before submission.</Alert></div>
      <Card title="Generated files" className="mt-6">
        <Table head={["#", "Created", "Type", "Analysis run", "Files"]} empty="Nothing generated yet."
          rows={(list.data ?? []).map((r) => [r.id, fmtDate(r.created_at), <Badge tone={r.kind === "final" ? "green" : r.kind === "presentation" ? "blue" : "amber"}>{r.kind}</Badge>, r.analysis_run_id ?? "—",
            <div className="flex flex-wrap gap-2">{r.files.map((f) => <Button key={f.name} variant="secondary" className="px-2 py-1 text-xs" onClick={() => adminDownload(`/reports/${r.id}/files/${f.name}`, f.name)}>{f.label}</Button>)}</div>])} />
      </Card>
    </>
  );
}
