import { useEffect, useMemo, useState } from "react";
import { admin, adminDownload, adminObjectUrl } from "../api";
import Plot from "../components/Plot";
import { Alert, Badge, Button, Card, Stat, Table } from "../components/ui";
import { PageTitle, fmtDate, useLoad } from "./ResearcherApp";

/* eslint-disable @typescript-eslint/no-explicit-any */
type R = any;
interface Run { id: number; created_at: string; status: string; n_participants_included: number; n_participants_total: number; results: R; error: string | null }

const C = ["A", "B", "C"] as const;
const LBL: Record<string, string> = { A: "Control", B: "Numerical", C: "Visual" };
const COL: Record<string, string> = { A: "#0072B2", B: "#E69F00", C: "#009E73" };
export const num = (x: unknown, d = 3) => (typeof x === "number" && isFinite(x) ? x.toFixed(d) : "—");
export const pfmt = (p: unknown) => (typeof p !== "number" ? "—" : p < 0.001 ? "< .001" : p.toFixed(3).replace(/^0/, ""));

export default function AnalysisPage() {
  const latest = useLoad(() => admin<Run | null>("GET", "/analysis/latest"));
  const [run, setRun] = useState<Run | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => { if (latest.data) setRun(latest.data); }, [latest.data]);

  const runNow = async () => {
    setBusy(true); setErr(null);
    try { setRun(await admin<Run>("POST", "/analysis/run")); }
    catch (e) { setErr(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  };
  const r = run?.results;
  return (
    <>
      <PageTitle title="Statistical analysis" subtitle="Runs the pre-specified analysis plan on all eligible main-study data (collected + imported). Pilot sessions and practice trials are excluded automatically."
        actions={<Button onClick={runNow} disabled={busy}>{busy ? "Running analysis…" : "Run Analysis"}</Button>} />
      {err && <div className="mb-4"><Alert kind="error">{err}</Alert></div>}
      {!r && !latest.loading && <Alert kind="info">No analysis has been run yet. Click <strong>Run Analysis</strong>. With no genuine data, the results will be marked as pending.</Alert>}
      {r && <Results run={run!} r={r} />}
    </>
  );
}

function Results({ run, r }: { run: Run; r: R }) {
  const m = r.meta;
  const inc = useMemo(() => (r.participant_summary as R[]).filter((p) => !p.excluded), [r]);
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Run" value={`#${run.id}`} hint={fmtDate(run.created_at)} />
        <Stat label="Included participants" value={m.n_included} hint={`target ${m.target_n}`} />
        <Stat label="Excluded" value={m.n_excluded} hint="pre-specified rules" />
        <Stat label="Status" value={<Badge tone={m.status === "ok" ? "green" : "amber"}>{m.status}</Badge>} hint={`dataset ${String(m.dataset_hash).slice(0, 10)}`} />
      </div>
      {m.messages.map((x: string, i: number) => <Alert key={i} kind="warn">{x}</Alert>)}

      {r.hypotheses && (
        <Card title="Hypothesis outcomes (automatically derived — review before reporting)">
          <Table head={["", "Hypothesis", "Decision", "Evidence"]} rows={r.hypotheses.map((h: R) => [
            <strong>{h.id}</strong>, <span className="whitespace-normal">{h.text}</span>,
            <Badge tone={h.decision.startsWith("supported") || h.decision === "rejected" ? "green" : h.decision === "not tested" ? "slate" : "amber"}>{h.decision}</Badge>,
            <span className="whitespace-normal text-xs">{h.detail}</span>])} />
          <p className="mt-2 text-xs text-slate-500">A non-significant result is not evidence that no effect exists. Holm correction across the three pairwise comparisons; α = {m.analysis_config.alpha}.</p>
        </Card>
      )}

      {inc.length > 0 && <Charts inc={inc} />}

      {r.confirmatory && (["accuracy", "rt"] as const).map((k) => <Confirmatory key={k} c={r.confirmatory[k]} pct={k === "accuracy"} />)}

      {r.descriptives && (
        <Card title="Descriptive statistics (participant level, eligible participants)">
          <Table head={["Measure", "Condition", "n", "Mean", "SD", "Median", "Min", "Max", "IQR", "95% CI"]}
            rows={Object.entries(r.descriptives).filter(([k]) => !["trial_level"].includes(k)).flatMap(([k, v]: [string, R]) => Object.entries(v).map(([c, d]: [string, R]) => [
              k, LBL[c] ?? c, d.n, num(d.mean), num(d.sd), num(d.median), num(d.min), num(d.max), num(d.iqr), d.ci_low != null ? `[${num(d.ci_low)}, ${num(d.ci_high)}]` : "—"]))} />
          {r.descriptives.trial_level && (
            <><h3 className="mt-5 font-semibold">Trial level (descriptive only — trials are not independent observations)</h3>
              <Table head={["Condition", "Trials", "Valid", "Accuracy", "Error rate", "Timeout rate", "Mean correct RT", "Median correct RT"]}
                rows={Object.entries(r.descriptives.trial_level).map(([c, d]: [string, R]) => [LBL[c], d.n_trials, d.n_valid, num(d.accuracy), num(d.error_rate), num(d.timeout_rate), num(d.mean_correct_rt, 1), num(d.median_correct_rt, 1)])} /></>
          )}
        </Card>
      )}

      {r.manipulation_check && Object.keys(r.manipulation_check).length > 0 && (
        <Card title="Manipulation check: secondary-task performance (B vs C)">
          <Table head={["Measure", "Mean B", "Mean C", "t", "df", "p", "d_z", "Wilcoxon p", "r_rb"]} rows={Object.entries(r.manipulation_check).map(([k, v]: [string, R]) => [
            k, num(v.t_test.mean_x), num(v.t_test.mean_y), num(v.t_test.t, 2), v.t_test.df ?? "—", pfmt(v.t_test.p), num(v.t_test.cohens_dz, 2), pfmt(v.wilcoxon.p), num(v.wilcoxon.rank_biserial, 2)])} />
          <p className="mt-2 text-xs text-slate-500">A significant difference means the two interference tasks were not matched in difficulty; consider this when interpreting H3.</p>
        </Card>
      )}

      {r.exploratory && <Exploratory e={r.exploratory} />}

      <Card title="Data quality and exclusions">
        <div className="grid gap-4 md:grid-cols-2">
          <pre className="max-h-80 overflow-auto rounded bg-slate-100 p-3 text-xs dark:bg-slate-950">{JSON.stringify(r.data_quality, null, 1)}</pre>
          <div>
            {r.exclusions.length === 0 ? <p className="text-sm">No participants excluded.</p> :
              <Table head={["Participant", "Rules", "Reasons"]} rows={r.exclusions.map((x: R) => [x.participant_id, x.rules.join(", "), <span className="whitespace-normal text-xs">{x.reasons.join("; ")}</span>])} />}
          </div>
        </div>
      </Card>

      <Figures run={run} figures={r.figures} />
    </div>
  );
}

function Charts({ inc }: { inc: R[] }) {
  const mk = (cols: Record<string, string>, scale: number, title: string, ylab: string) => {
    const data: R[] = [];
    C.forEach((c) => {
      const v = inc.map((p) => p[cols[c]]).filter((x) => typeof x === "number").map((x: number) => x * scale);
      const n = v.length, mean = v.reduce((a: number, b: number) => a + b, 0) / (n || 1);
      const sd = Math.sqrt(v.reduce((a: number, b: number) => a + (b - mean) ** 2, 0) / Math.max(1, n - 1));
      const ci = n > 1 ? 1.96 * sd / Math.sqrt(n) : 0;
      data.push({ type: "box", y: v, name: LBL[c], boxpoints: "all", jitter: 0.4, pointpos: 0, marker: { color: COL[c], size: 5 }, line: { color: COL[c] }, fillcolor: "rgba(0,0,0,0)", hoverinfo: "y" });
      data.push({ type: "scatter", x: [LBL[c]], y: [mean], error_y: { type: "data", array: [ci], visible: true, color: "#000" }, mode: "markers", marker: { color: "#000", size: 10, symbol: "diamond" }, name: `${LBL[c]} mean ± ~95% CI`, showlegend: false });
    });
    return <Plot data={data} layout={{ title: { text: title }, yaxis: { title: { text: ylab } }, showlegend: false }} height={340} />;
  };
  const lines = (cols: Record<string, string>, scale: number, ylab: string) => (
    <Plot data={inc.map((p) => ({ type: "scatter", mode: "lines+markers", x: C.map((c) => LBL[c]), y: C.map((c) => p[cols[c]] == null ? null : p[cols[c]] * scale), name: p.participant_id, line: { color: "rgba(100,100,100,0.4)" }, marker: { size: 4 } }))}
      layout={{ title: { text: "Paired participant profiles" }, yaxis: { title: { text: ylab } }, showlegend: false }} height={340} />
  );
  const ACC = { A: "control_accuracy", B: "numerical_accuracy", C: "visual_accuracy" };
  const RT = { A: "control_mean_correct_rt_ms", B: "numerical_mean_correct_rt_ms", C: "visual_mean_correct_rt_ms" };
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title={`Accuracy by condition (N = ${inc.length})`}>{mk(ACC, 100, "Recognition accuracy", "% correct")}</Card>
      <Card title="Mean correct RT by condition">{mk(RT, 1, "Mean correct RT", "ms")}</Card>
      <Card title="Paired accuracy">{lines(ACC, 100, "% correct")}</Card>
      <Card title="Interference costs (positive = worse than control)">
        <Plot data={[
          { type: "box", y: inc.map((p) => p.numerical_accuracy_cost * 100), name: "Numerical acc. cost (pp)", boxpoints: "all", marker: { color: COL.B } },
          { type: "box", y: inc.map((p) => p.visual_accuracy_cost * 100), name: "Visual acc. cost (pp)", boxpoints: "all", marker: { color: COL.C } },
        ]} layout={{ yaxis: { title: { text: "Percentage points" }, zeroline: true }, showlegend: false }} height={340} />
      </Card>
    </div>
  );
}

function Confirmatory({ c, pct }: { c: R; pct: boolean }) {
  if (!c) return null;
  return (
    <Card title={`Confirmatory analysis — ${c.dv}`}>
      {c.status !== "ok" ? <Alert kind="warn">{c.note}</Alert> : (
        <>
          <Alert kind="info"><strong>Test selection:</strong> {c.route_reason}</Alert>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <h3 className="font-semibold">Omnibus</h3>
              <Table head={["Test", "Statistic", "df", "p", "Effect size"]} rows={[
                [`RM-ANOVA${c.route === "parametric" ? " (primary)" : ""}`, `F = ${num(c.rm_anova.F, 2)}`, `${c.rm_anova.df1}, ${c.rm_anova.df2}`, pfmt(c.rm_anova.p), `ηp² = ${num(c.rm_anova.partial_eta_sq, 3)}`],
                ["RM-ANOVA, Greenhouse–Geisser", `ε = ${num(c.rm_anova.sphericity?.gg_epsilon, 3)}`, `${num(c.rm_anova.gg_df1, 2)}, ${num(c.rm_anova.gg_df2, 2)}`, pfmt(c.rm_anova.p_gg), ""],
                [`Friedman${c.route === "nonparametric" ? " (primary)" : ""}`, `χ² = ${num(c.friedman.chi2, 2)}`, c.friedman.df ?? "—", pfmt(c.friedman.p), `W = ${num(c.friedman.kendalls_w, 3)}`],
              ]} />
              <p className="mt-2 text-xs">Mauchly's W = {num(c.rm_anova.sphericity?.W, 3)}, p = {pfmt(c.rm_anova.sphericity?.p)}. Shapiro–Wilk on differences: {Object.entries(c.normality).map(([k, v]: [string, R]) => `${k}: p = ${pfmt(v.p)}`).join("; ")}. {pct && `Ceiling (100% accuracy): ${Object.entries(c.ceiling).map(([k, v]) => `${k} ${Math.round(Number(v) * 100)}%`).join(", ")}.`}</p>
            </div>
            <div>
              <h3 className="font-semibold">Pairwise (Holm-corrected)</h3>
              <Table head={["Pair", "Mean diff [95% CI]", "t (df)", "p Holm", "d_z", "Wilcoxon p Holm", "r_rb"]} rows={c.pairwise.map((p: R) => [
                <span>{p.pair} <span className="text-xs text-slate-500">({p.hypothesis})</span></span>,
                `${num(p.t_test.mean_diff, pct ? 3 : 1)} [${num(p.t_test.ci_low, pct ? 3 : 1)}, ${num(p.t_test.ci_high, pct ? 3 : 1)}]`,
                `${num(p.t_test.t, 2)} (${p.t_test.df ?? "—"})`,
                <span className={p.primary === "t_test" ? "font-bold" : ""}>{pfmt(p.t_test.p_holm)}</span>, num(p.t_test.cohens_dz, 2),
                <span className={p.primary === "wilcoxon" ? "font-bold" : ""}>{pfmt(p.wilcoxon.p_holm)}</span>, num(p.wilcoxon.rank_biserial, 2)])} />
              <p className="mt-2 text-xs text-slate-500">Bold = primary test for this dependent variable.</p>
            </div>
          </div>
        </>
      )}
    </Card>
  );
}

function Exploratory({ e }: { e: R }) {
  return (
    <Card title="Exploratory analyses (RQ2) — associations only, no causal interpretation">
      <h3 className="font-semibold">Correlations</h3>
      <Table head={["Variables", "Method", "r / ρ", "95% CI", "p", "n", "Why this method"]} rows={e.correlations.map((c: R) => [
        c.label, c.method ?? "—", num(c.r, 2), c.ci_low != null ? `[${num(c.ci_low, 2)}, ${num(c.ci_high, 2)}]` : "—", pfmt(c.p), c.n, <span className="whitespace-normal text-xs">{c.method_reason ?? c.note ?? ""}</span>])} />
      {(["gender", "academic_course"] as const).map((v) => e.demographics?.[v] && (
        <div key={v} className="mt-5">
          <h3 className="font-semibold">{v === "gender" ? "Gender" : "Academic course"}</h3>
          <p className="text-sm">Group sizes: {Object.entries(e.demographics[v].counts).map(([k, n]) => `${k} ${n}`).join(", ")}</p>
          {e.demographics[v].note && <p className="text-xs text-amber-700 dark:text-amber-400">{e.demographics[v].note}</p>}
          {Object.entries(e.demographics[v].tests ?? {}).map(([dv, t]: [string, R]) => (
            <p key={dv} className="text-xs">{dv}: {t.welch_t ? `Welch t = ${num(t.welch_t.t, 2)}, p = ${pfmt(t.welch_t.p)}, g = ${num(t.welch_t.hedges_g, 2)}; Mann–Whitney p = ${pfmt(t.mann_whitney.p)}` :
              `Welch F = ${num(t.welch_anova?.F, 2)}, p = ${pfmt(t.welch_anova?.p)}, η² = ${num(t.welch_anova?.eta_sq, 3)}; Kruskal–Wallis p = ${pfmt(t.kruskal_wallis?.p)}, ε² = ${num(t.kruskal_wallis?.epsilon_sq, 3)}`}</p>
          ))}
        </div>
      ))}
      {e.block_position && (
        <p className="mt-5 text-sm"><strong>Block position (order/fatigue):</strong> accuracy {Object.entries(e.block_position.accuracy.descriptives).map(([k, d]: [string, R]) => `block ${k} ${num(d.mean)}`).join(", ")}; Friedman p = {pfmt(e.block_position.accuracy.friedman?.p)}.</p>
      )}
      {e.ies && <p className="mt-2 text-sm"><strong>IES</strong> available for {e.ies.n_with_ies} participant(s). {e.ies.note}</p>}
    </Card>
  );
}

function Figures({ run, figures }: { run: Run; figures: R[] }) {
  const [urls, setUrls] = useState<Record<string, string>>({});
  useEffect(() => {
    let alive = true;
    figures.filter((f) => f.available).forEach((f) => adminObjectUrl(`/analysis/${run.id}/figures/${f.files.png}`).then((u) => alive && setUrls((x) => ({ ...x, [f.id]: u }))).catch(() => undefined));
    return () => { alive = false; };
  }, [run.id, figures]);
  return (
    <Card title="Publication figures" actions={figures.some((f) => f.available) && <Button variant="secondary" onClick={() => adminDownload(`/analysis/${run.id}/figures.zip`, "figures.zip")}>Download all (zip)</Button>}>
      {figures.length === 0 && <p className="text-sm text-slate-500">No figures — no eligible data yet.</p>}
      <div className="grid gap-6 md:grid-cols-2">
        {figures.map((f) => (
          <figure key={f.id} className="rounded-lg border border-slate-200 p-3 dark:border-slate-800">
            <figcaption className="mb-2 flex flex-wrap items-center justify-between gap-2 text-sm font-semibold">
              <span>{f.title}</span>
              {f.available && <span className="flex gap-2 text-xs font-normal">{(["png", "svg", "pdf"] as const).map((x) => <button key={x} className="text-blue-700 underline dark:text-blue-400" onClick={() => adminDownload(`/analysis/${run.id}/figures/${f.files[x]}`, f.files[x])}>{x.toUpperCase()}</button>)}</span>}
            </figcaption>
            {f.available ? (urls[f.id] ? <img src={urls[f.id]} alt={f.title} className="w-full rounded bg-white" /> : <p className="text-xs">Loading…</p>) : <p className="text-xs text-slate-500">Not generated: {f.note}</p>}
          </figure>
        ))}
      </div>
    </Card>
  );
}
