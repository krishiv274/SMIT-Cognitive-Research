import { useEffect, useState } from "react";
import { admin } from "../api";
import { Alert, Button, Card, Field, inputCls } from "../components/ui";
import { PageTitle, useLoad } from "./ResearcherApp";

const GROUPS: { title: string; note?: string; keys: [string, string, boolean?][] }[] = [
  { title: "Report title page", keys: [["university_name", "University"], ["department", "Department"], ["course_name", "Course name"], ["student_names", "Student names"], ["professor_name", "Professor"], ["submission_date", "Submission date"]] },
  { title: "Consent form & contact (shown to participants)", note: "Never state that institutional ethics approval was granted unless it actually was.", keys: [["researcher_contact", "Researcher contact email"], ["supervisor_contact", "Supervisor contact email"], ["ethics_statement", "Ethics status statement", true], ["withdrawal_deadline", "Data-withdrawal deadline"], ["data_storage_statement", "Data storage statement", true], ["retention_statement", "Data retention statement", true]] },
  { title: "Method details for the report", keys: [["apparatus", "Apparatus (computer, OS, browser, monitor, keyboard)", true], ["recruitment_description", "Recruitment description", true]] },
  { title: "Human pilot testing (written by the research team)", note: "Record genuine human pilot observations only. Automated software tests are reported separately and are not pilot testing.", keys: [["pilot_observations", "Pilot observations", true], ["pilot_design_changes", "Design changes made after piloting", true]] },
  { title: "Deviations from the analysis plan", keys: [["deviations_from_plan", "Deviations (leave blank if none)", true]] },
];

export default function SettingsPage() {
  const { data, error } = useLoad(() => admin<Record<string, string>>("GET", "/settings"));
  const [v, setV] = useState<Record<string, string>>({});
  const [msg, setMsg] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  const [saved, setSaved] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (data) { setV(data); setSaved(data); } }, [data]);
  const dirty = Object.keys(v).some((k) => (v[k] ?? "") !== (saved[k] ?? ""));
  // Warn before leaving the page with unsaved changes.
  useEffect(() => {
    if (!dirty) return;
    const h = (e: BeforeUnloadEvent) => { e.preventDefault(); };
    window.addEventListener("beforeunload", h);
    return () => window.removeEventListener("beforeunload", h);
  }, [dirty]);
  const save = async () => {
    setBusy(true);
    try { const r = await admin<Record<string, string>>("PUT", "/settings", v); setV(r); setSaved(r); setMsg({ kind: "success", text: "Settings saved." }); }
    catch (e) { setMsg({ kind: "error", text: e instanceof Error ? e.message : String(e) }); }
    finally { setBusy(false); }
  };
  const set = (k: string, val: string) => { setV({ ...v, [k]: val }); if (msg?.kind === "success") setMsg(null); };
  if (error) return <Alert kind="error">{error}</Alert>;
  if (!data) return <p>Loading…</p>;
  return (
    <>
      <PageTitle title="Settings" subtitle="Institutional details, consent placeholders, report title page and pilot notes. Values in [brackets] are placeholders." actions={<>{dirty && <span className="text-sm text-amber-700 dark:text-amber-400">Unsaved changes</span>}<Button onClick={save} disabled={busy || !dirty}>{busy ? "Saving…" : "Save settings"}</Button></>} />
      {msg && <div className="mb-4"><Alert kind={msg.kind}>{msg.text}</Alert></div>}
      <div className="space-y-6">
        {GROUPS.map((g) => (
          <Card key={g.title} title={g.title}>
            {g.note && <div className="mb-4"><Alert kind="info">{g.note}</Alert></div>}
            <div className="grid gap-4 md:grid-cols-2">
              {g.keys.map(([k, label, long]) => (
                <div key={k} className={long ? "md:col-span-2" : ""}>
                  <Field label={label}>
                    {long ? <textarea className={inputCls} rows={k.startsWith("pilot") ? 6 : 3} value={v[k] ?? ""} onChange={(e) => set(k, e.target.value)} />
                      : <input className={inputCls} value={v[k] ?? ""} onChange={(e) => set(k, e.target.value)} />}
                  </Field>
                </div>
              ))}
            </div>
          </Card>
        ))}
      </div>
      {msg && <div className="mt-6"><Alert kind={msg.kind}>{msg.text}</Alert></div>}
      <div className="mt-6 flex items-center gap-3"><Button onClick={save} disabled={busy || !dirty}>{busy ? "Saving…" : "Save settings"}</Button>{dirty && <span className="text-sm text-amber-700 dark:text-amber-400">Unsaved changes</span>}</div>
    </>
  );
}
