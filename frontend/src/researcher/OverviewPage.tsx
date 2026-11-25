import { Link } from "react-router-dom";
import { admin } from "../api";
import Plot from "../components/Plot";
import { Alert, Card, Stat } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";

interface Overview {
  target_participants: number;
  registered_participants: number;
  completed_participants: number;
  incomplete_sessions: number;
  withdrawn_participants: number;
  excluded_participants: number;
  valid_experimental_trials: number;
  total_experimental_trials: number;
  pilot_sessions: number;
  imported_summary_only_participants: number;
  condition_order_distribution: Record<string, number>;
  gender_distribution: Record<string, number>;
  course_distribution: Record<string, number>;
  age_values: number[];
  progress_percent: number;
  active_config: { id: number; experiment_version: string; locked_at: string } | null;
}

export default function OverviewPage() {
  const { data, error } = useLoad(() => admin<Overview>("GET", "/overview"));
  if (error) return <Alert kind="error">{error}</Alert>;
  if (!data) return <p>Loading…</p>;
  const orders = Object.entries(data.condition_order_distribution);
  return (
    <>
      <PageTitle title="Overview" subtitle="Data-collection progress for the main study (pilot data are counted separately)." />
      {!data.active_config ? (
        <div className="mb-6"><Alert kind="warn">The main study is <strong>not open</strong>: no configuration is locked. Run pilot tests, then lock a configuration in <Link className="underline" to="/researcher/configuration">Configuration</Link>.</Alert></div>
      ) : (
        <div className="mb-6"><Alert kind="success">Main study open with locked configuration <strong className="font-mono">{data.active_config.experiment_version}</strong> (locked {fmtDate(data.active_config.locked_at)}).</Alert></div>
      )}
      <Card title="Progress towards the target sample" className="mb-6">
        <div className="flex items-end justify-between text-sm">
          <span><strong className="text-2xl">{data.completed_participants}</strong> of {data.target_participants} eligible completed participants</span>
          <span>{data.progress_percent}%</span>
        </div>
        <div className="mt-2 h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800" role="progressbar" aria-valuenow={data.progress_percent} aria-valuemin={0} aria-valuemax={100}>
          <div className="h-full bg-blue-700" style={{ width: `${data.progress_percent}%` }} />
        </div>
      </Card>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Registered" value={data.registered_participants} hint="main-study participants" />
        <Stat label="Completed" value={data.completed_participants} hint="active, completed or summary-imported" />
        <Stat label="Incomplete sessions" value={data.incomplete_sessions} hint="registered / in progress / incomplete / abandoned" />
        <Stat label="Valid trials" value={`${data.valid_experimental_trials}`} hint={`of ${data.total_experimental_trials} experimental trials`} />
        <Stat label="Withdrawn" value={data.withdrawn_participants} />
        <Stat label="Excluded" value={data.excluded_participants} />
        <Stat label="Pilot sessions" value={data.pilot_sessions} hint="never included in analysis" />
        <Stat label="Summary-only imports" value={data.imported_summary_only_participants} />
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card title="Condition-order distribution (counterbalancing)">
          <Plot data={[{ type: "bar", x: orders.map((o) => o[0]), y: orders.map((o) => o[1]), marker: { color: "#1F3A93" } }]}
            layout={{ xaxis: { title: { text: "Block order" } }, yaxis: { title: { text: "Participants" }, dtick: 1 } }} height={260} />
        </Card>
        <Card title="Age distribution">
          {data.age_values.length ? (
            <Plot data={[{ type: "histogram", x: data.age_values, marker: { color: "#56B4E9" } }]} layout={{ xaxis: { title: { text: "Age (years)" } }, yaxis: { title: { text: "Participants" } } }} height={260} />
          ) : <p className="text-sm text-slate-500">No participants yet.</p>}
        </Card>
        <Card title="Gender">
          <Distribution d={data.gender_distribution} />
        </Card>
        <Card title="Academic course">
          <Distribution d={data.course_distribution} />
        </Card>
      </div>
    </>
  );
}

function Distribution({ d }: { d: Record<string, number> }) {
  const e = Object.entries(d).sort((a, b) => b[1] - a[1]);
  if (!e.length) return <p className="text-sm text-slate-500">No participants yet.</p>;
  const max = Math.max(...e.map((x) => x[1]));
  return (
    <ul className="space-y-2">
      {e.map(([k, v]) => (
        <li key={k} className="text-sm">
          <div className="flex justify-between"><span>{k}</span><span className="tabular-nums">{v}</span></div>
          <div className="mt-1 h-2 rounded bg-slate-200 dark:bg-slate-800"><div className="h-2 rounded bg-pink-600" style={{ width: `${(100 * v) / max}%` }} /></div>
        </li>
      ))}
    </ul>
  );
}
