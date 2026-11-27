"""Builds the SMIT research report as a Document.

* PRELIMINARY report (no eligible genuine data): all theoretical and
  methodological sections complete; Results, Discussion and data-dependent
  conclusions explicitly marked as pending.
* FINAL report: Results populated from the analysis run; Discussion and
  Conclusion generated from the actual results with explicit review flags.

No sentence about findings is hard-coded: every result statement is built from
numbers in the analysis results dictionary.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..data_dictionary import CONTACT_VARS, PARTICIPANT_VARS, SESSION_VARS, TRIAL_VARS
from ..experiment.config import ExperimentConfig
from ..settings import REPO_ROOT
from .document import Bullets, Document, Figure, Heading, PageBreak, Para, Table, from_markdown

TITLE = ("Investigating the Effects of Numerical and Visual Interference on Spatial Working Memory "
         "and Cognitive Performance Among University Students")
RESEARCH = REPO_ROOT / "research"
COND = {"A": "Control", "B": "Numerical interference", "C": "Visual interference"}
PENDING = ("PENDING — this section will be generated automatically from genuine participant data after data "
           "collection and analysis. No results are reported in this preliminary version.")


def _md(name: str, **kw) -> list:
    p = RESEARCH / name
    return from_markdown(p.read_text(encoding="utf-8"), **kw) if p.exists() else [Para(f"[{name} not found]", "warning")]


def n(x, d=2):
    return "—" if x is None else f"{x:.{d}f}"


def pf(p):
    if p is None:
        return "—"
    return "< .001" if p < 0.001 else f"{p:.3f}".lstrip("0")


def pe(p):
    """'p = .012' or 'p < .001'."""
    if p is None:
        return "p = n/a"
    return "p < .001" if p < 0.001 else f"p = {pf(p)}"


def pct(x, d=1):
    return "—" if x is None else f"{100 * x:.{d}f}%"


def _settings_val(settings: dict, k: str) -> str:
    return settings.get(k) or f"[{k.upper()}]"


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------

def title_page(doc: Document, settings: dict, final: bool, results: dict | None) -> None:
    doc.add(Para(TITLE, "title"),
            Para("SMIT — Spatial Memory Interference Task", "subtitle"),
            Para("FINAL RESEARCH REPORT (data-dependent sections generated from the analysed dataset — review required)"
                 if final else "PRELIMINARY RESEARCH PROTOCOL / REPORT — results pending genuine data collection", "subtitle"),
            Para(" ", "center"))
    rows = [["University", _settings_val(settings, "university_name")], ["Department", _settings_val(settings, "department")],
            ["Course", _settings_val(settings, "course_name")], ["Student names", _settings_val(settings, "student_names")],
            ["Professor", _settings_val(settings, "professor_name")],
            ["Submission date", _settings_val(settings, "submission_date")],
            ["Report generated", date.today().isoformat()]]
    if results:
        m = results["meta"]
        rows += [["Analysis dataset", f"hash {m['dataset_hash'][:12]}; {m['n_included']} eligible participants"],
                 ["Experiment version(s)", ", ".join(m["experiment_versions"]) or "—"]]
    doc.add(Table(["Item", "Details"], rows, widths=[1, 3]), PageBreak())


def abstract(doc: Document, cfg: ExperimentConfig, results: dict | None, final: bool) -> None:
    tr = cfg.trials
    doc.h("Abstract", 1)
    obj = ("**Objective.** This study examined how numerical (arithmetic verification) and visual (spatial symmetry judgement) "
           "interference during the retention interval affect spatial working-memory recognition accuracy and reaction time in "
           "university students.")
    meth = ("**Method.** In a within-subjects design, participants memorised four highlighted cells in a 3×3 grid (500 ms), "
            "performed no task (control), an arithmetic verification or a symmetry judgement during a 3,000 ms interference phase, "
            "and after a further 1,000 ms decided whether a probe grid was identical to the memorised pattern. Each participant "
            f"completed {3 * tr.trials_per_condition} experimental trials ({tr.trials_per_condition} per condition) "
            "in a fully counterbalanced block order.")
    if not final or not results:
        doc.add(Para(obj), Para(meth), Para("**Results and conclusion.** " + PENDING, "pending"))
        return
    m = results["meta"]
    acc = results["confirmatory"]["accuracy"]
    rt = results["confirmatory"]["rt"]
    d = results["descriptives"]["accuracy"]
    parts = [f"**Participants.** {m['n_included']} eligible participants were analysed "
             f"({m['n_excluded']} excluded under pre-specified rules)."]
    if acc.get("status") == "ok":
        parts.append(f"**Results.** Mean accuracy was {pct(d['A']['mean'])} (control), {pct(d['B']['mean'])} (numerical) and "
                     f"{pct(d['C']['mean'])} (visual). The omnibus {acc['omnibus']['test']} on accuracy gave {pe(acc['omnibus']['p'])}; "
                     f"the omnibus test on mean correct RT gave {pe(rt['omnibus']['p']) if rt.get('status') == 'ok' else 'n/a'}.")
    hyp = results.get("hypotheses", [])
    sup = [h["id"] for h in hyp if h["decision"] == "supported"]
    parts.append("**Conclusion.** " + (f"Hypotheses supported: {', '.join(sup)}. " if sup else "None of the directional hypotheses was supported. ")
                 + "See the Discussion for interpretation and limitations (automatically drafted; to be reviewed by the authors).")
    doc.add(Para(obj), Para(meth), *[Para(x) for x in parts])


def methodology(doc: Document, cfg: ExperimentConfig, settings: dict, results: dict | None, stimdir: Path) -> None:
    t, tr = cfg.timing, cfg.trials
    doc.h("Methodology", 1)
    doc.h("Experimental design", 2)
    doc.p("A one-factor (interference condition: control, numerical, visual) within-subjects repeated-measures design was used. "
          "Every participant completed all three conditions in blocks whose order was fully counterbalanced across the six possible orders.")
    doc.h("Participants and recruitment", 2)
    doc.p(settings.get("recruitment_description") or "[Recruitment description]")
    doc.p("**Inclusion criteria:** age 18 or older; normal or corrected-to-normal vision; able to use a keyboard; informed consent. "
          "**Exclusion criteria before testing:** previous participation in the pilot; self-reported photosensitive epilepsy; difficulty "
          "distinguishing blue from orange. **Analysis exclusions** were pre-specified (Statistical Analysis Plan §4).")
    if results and results.get("sample"):
        s = results["sample"]
        a = s["age"]
        doc.p(f"The analysed sample comprised **{s['n']} participants** (age M = {n(a.get('mean'), 1)}, SD = {n(a.get('sd'), 1)}, "
              f"range {n(a.get('min'), 0)}–{n(a.get('max'), 0)} years). Gender: "
              + ", ".join(f"{k} {v}" for k, v in s["gender"].items()) + ". Courses: "
              + ", ".join(f"{k} {v}" for k, v in s["academic_course"].items()) + ".")
    else:
        doc.p("Participant characteristics: " + PENDING, "pending")
    doc.h("Apparatus and software", 2)
    doc.p(settings.get("apparatus") or "[Apparatus]")
    doc.p("The task was implemented as a local web application (React/TypeScript front end; Python/FastAPI back end; SQLite database). "
          "Stimuli were drawn on an HTML canvas synchronised to the display refresh with requestAnimationFrame; durations were converted to "
          "whole frames and the actual duration of every phase was measured and stored. Reaction times used the browser's "
          "high-resolution event timestamps. Timing precision is browser-grade, not laboratory-grade (Anwyl-Irvine et al., 2021; Bridges et al., 2020).")
    doc.h("Stimuli and conditions", 2)
    doc.add(Table(["Element", "Specification"], [
        ["Memory/probe grid", f"{cfg.grid.size}×{cfg.grid.size} grid, {cfg.grid.cell_size_px} px cells, {cfg.grid.highlight_count} cells filled blue ({cfg.grid.memory_highlight_color}) on mid-grey"],
        ["Different probe", f"exactly one filled cell moved to an empty position (change type: {tr.change_type}); number of filled cells constant"],
        ["A — Control", "blank screen with a central dot during the interference phase (no secondary task)"],
        ["B — Numerical", f"single-digit addition verification ({cfg.secondary_tasks.numerical.operand_min}–{cfg.secondary_tasks.numerical.operand_max}), 50% true; F = true, J = false"],
        ["C — Visual", f"new grid with {cfg.secondary_tasks.visual.highlight_count} orange cells; {cfg.secondary_tasks.visual.probe} judgement, 50% yes; F = yes, J = no; generated independently of the memory pattern"],
        ["Responses", f"F = same, J = different; deadline {t.recognition_deadline_ms} ms"],
    ], caption="Table 1. Stimuli and conditions", widths=[1, 3]))
    doc.h("Timing parameters", 2)
    isi = t.post_stimulus_blank_ms + t.interference_ms + t.retention_ms
    doc.add(Table(["Phase", "Duration", "Frames at 60 Hz"], [
        ["Fixation", f"{t.fixation_ms} ms", f"{t.fixation_ms / (1000 / 60):.1f}"],
        ["Memory stimulus", f"{t.memory_stimulus_ms} ms", f"{t.memory_stimulus_ms / (1000 / 60):.1f}"],
        ["Post-stimulus blank", f"{t.post_stimulus_blank_ms} ms", f"{t.post_stimulus_blank_ms / (1000 / 60):.1f}"],
        ["Interference", f"{t.interference_ms} ms", f"{t.interference_ms / (1000 / 60):.1f}"],
        ["Retention", f"{t.retention_ms} ms", f"{t.retention_ms / (1000 / 60):.1f}"],
        ["Recognition window", f"≤ {t.recognition_deadline_ms} ms", "—"],
        ["ITI", f"{t.iti_min_ms}–{t.iti_max_ms} ms (uniform jitter)", "—"],
        ["ISI memory → probe", f"{isi} ms", "—"], ["SOA memory → probe", f"{t.memory_stimulus_ms + isi} ms", "—"],
    ], caption="Table 2. Trial timing (configuration " + cfg.name + ")"))
    doc.add(Figure(stimdir / "temporal_layout.png", "Figure M1. Temporal layout of a trial."),
            Figure(stimdir / "stimulus_sequence.png", "Figure M2. Stimulus illustrations for each phase and condition."))
    doc.h("Procedure and counterbalancing", 2)
    doc.p(f"After consent and registration, participants read illustrated instructions and completed {3 * tr.practice_per_condition} practice "
          f"trials with feedback (repeatable up to {tr.max_practice_repeats} times), followed by three blocks of {tr.trials_per_condition} trials "
          f"(no feedback) separated by breaks of at least {t.break_min_s} s. Within each block, same and different trials were balanced "
          f"({round(tr.trials_per_condition * tr.same_proportion)} each) and randomly ordered with at most {tr.max_same_answer_run} consecutive "
          "identical answers. No memory pattern was repeated within a session. Block order was assigned with a persistent least-used rule "
          "over all six orders; each session's random seed and full trial plan were stored for reproducibility.")
    doc.add(Figure(stimdir / "task_flow.png", "Figure M3. Participant task flow."))
    doc.h("Variables", 2)
    doc.add(Table(["Role", "Variable"], [
        ["Independent variable", "Interference condition (A control, B numerical, C visual), within subjects"],
        ["Primary DVs", "Recognition accuracy (proportion correct; timeouts = errors); mean correct recognition RT (ms)"],
        ["Secondary DVs", "Timeout rate, hit/false-alarm rates, d′, Pashler's K, IES, interference costs (positive = worse)"],
        ["Manipulation check", "Secondary-task accuracy and RT (B, C)"],
        ["Exploratory", "Age, gender, academic course; block position"],
    ], widths=[1, 3]))
    doc.h("Data collection and ethics", 2)
    doc.p("Data were saved to the local database after every trial (with a browser-side retry queue). Email addresses were stored in a "
          "separate table and never included in analyses, exports or this report. " + (settings.get("ethics_statement") or ""))
    doc.h("Statistical analysis plan", 2)
    doc.p("The analysis followed the pre-specified Statistical Analysis Plan (Appendix F). In summary: participant-level aggregation; "
          "Shapiro–Wilk tests on paired differences and a ceiling check select between repeated-measures ANOVA (Mauchly test, "
          "Greenhouse–Geisser correction) with paired t-tests, and the Friedman test with Wilcoxon signed-rank tests; Holm correction "
          "across the three pairwise comparisons per DV; effect sizes d_z, partial η², rank-biserial r and Kendall's W; exploratory "
          "Pearson/Spearman correlations with 95% CIs; Welch's t / Welch ANOVA (with nonparametric alternatives) for demographic groups "
          "with at least 5 participants; α = .05.")


def cognitive_task_design(doc: Document) -> None:
    doc.h("Cognitive Task Design: Application of Lecture Concepts", 1)
    blocks = _md("Experimental_Design.md", base_level=2)
    # include sections 5 and 6 (task components and design threats)
    keep, on = [], False
    for b in blocks:
        if isinstance(b, Heading) and b.level == 2:
            on = b.text.startswith("5.") or b.text.startswith("6.")
        if on:
            keep.append(b)
    doc.add(keep)
    doc.h("Lecture concept mapping", 2)
    mp = _md("Lecture_Concept_Mapping.md", base_level=3)
    tables = [b for b in mp if isinstance(b, Table)]
    if len(tables) >= 2:
        tables[1].caption = "Table 3. Design decisions mapped to the Week 14 lecture ([Lecture] / [Literature] / [Design])"
        doc.add(tables[1])


def pilot_section(doc: Document, settings: dict) -> None:
    doc.h("Pilot Testing", 1)
    doc.h("Automated technical testing (software verification — not human pilot testing)", 2)
    dr = REPO_ROOT / "pilot" / "Technical_Dry_Run_Report.md"
    if dr.exists():
        txt = dr.read_text(encoding="utf-8")
        summ = []
        for b in from_markdown(txt, base_level=3):
            if isinstance(b, Table):
                b.caption = "Automated test results (see pilot/Technical_Dry_Run_Report.md)"
                summ.append(b)
                break
        doc.add(summ or [Para("See pilot/Technical_Dry_Run_Report.md.")])
    doc.p("These tests used synthetic, software-generated data in isolated temporary databases; they verify the software only and "
          "provide no information about human performance.", "note")
    doc.h("Human pilot testing", 2)
    obs = (settings.get("pilot_observations") or "").strip()
    if obs:
        doc.p(obs)
    else:
        doc.p("[PENDING — to be completed by the research team after human pilot testing with 3–5 volunteers following the protocol in "
              "Appendix G. Record observations in the dashboard: Settings → Pilot observations.]", "pending")
    doc.h("Design changes resulting from piloting", 2)
    ch = (settings.get("pilot_design_changes") or "").strip()
    doc.p(ch if ch else "[PENDING — describe any parameter changes and their justification, or state that none were needed.]",
          "normal" if ch else "pending")


def _desc_table(results: dict) -> Table:
    d = results["descriptives"]
    rows = []
    for label, key, fmt in (("Accuracy (proportion)", "accuracy", 3), ("Mean correct RT (ms)", "mean_correct_rt_ms", 1),
                            ("Median correct RT (ms)", "median_correct_rt_ms", 1), ("Timeout rate", "timeout_rate", 3),
                            ("d′", "dprime", 2)):
        if key not in d:
            continue
        for c in "ABC":
            s = d[key].get(c, {})
            if not s.get("n"):
                continue
            rows.append([label, COND[c], s["n"], n(s.get("mean"), fmt), n(s.get("sd"), fmt), n(s.get("median"), fmt),
                         f"{n(s.get('min'), fmt)}–{n(s.get('max'), fmt)}", n(s.get("iqr"), fmt),
                         f"[{n(s.get('ci_low'), fmt)}, {n(s.get('ci_high'), fmt)}]"])
    return Table(["Measure", "Condition", "n", "M", "SD", "Mdn", "Range", "IQR", "95% CI"], rows,
                 caption="Table 4. Descriptive statistics (participant level)")


def _confirm_tables(c: dict, label: str, num: int) -> list:
    if c.get("status") != "ok":
        return [Para(f"{label}: {c.get('note')}", "pending")]
    a, f = c["rm_anova"], c["friedman"]
    sph = a.get("sphericity", {})
    out = [Para(f"**Test selection ({label}).** {c['route_reason']}"),
           Table(["Test", "Statistic", "df", "p", "Effect size"], [
               ["Repeated-measures ANOVA" + (" (primary)" if c["route"] == "parametric" else ""), f"F = {n(a.get('F'))}", f"{a.get('df1')}, {a.get('df2')}", pf(a.get("p")), f"ηp² = {n(a.get('partial_eta_sq'), 3)}"],
               ["Greenhouse–Geisser corrected", f"ε = {n(sph.get('gg_epsilon'), 3)}", f"{n(a.get('gg_df1'))}, {n(a.get('gg_df2'))}", pf(a.get("p_gg")), ""],
               ["Mauchly's test of sphericity", f"W = {n(sph.get('W'), 3)}", str(sph.get("df", "—")), pf(sph.get("p")), ""],
               ["Friedman test" + (" (primary)" if c["route"] == "nonparametric" else ""), f"χ² = {n(f.get('chi2'))}", str(f.get("df", "—")), pf(f.get("p")), f"W = {n(f.get('kendalls_w'), 3)}"],
           ], caption=f"Table {num}a. Omnibus tests — {label}"),
           Table(["Comparison", "H", "Mean diff [95% CI]", "t (df)", "p (Holm)", "d_z", "Wilcoxon W", "p (Holm)", "r_rb"],
                 [[p["label"], p["hypothesis"], f"{n(p['t_test'].get('mean_diff'), 3)} [{n(p['t_test'].get('ci_low'), 3)}, {n(p['t_test'].get('ci_high'), 3)}]",
                   f"{n(p['t_test'].get('t'))} ({p['t_test'].get('df', '—')})", pf(p["t_test"].get("p_holm")), n(p["t_test"].get("cohens_dz")),
                   n(p["wilcoxon"].get("W"), 1), pf(p["wilcoxon"].get("p_holm")), n(p["wilcoxon"].get("rank_biserial"))] for p in c["pairwise"]],
                 caption=f"Table {num}b. Pairwise comparisons — {label} (primary test: {'paired t' if c['route'] == 'parametric' else 'Wilcoxon'})",
                 widths=[2.6, 0.5, 2.4, 1.2, 0.9, 0.7, 1.0, 0.9, 0.7]),
           Para("Normality of paired differences (Shapiro–Wilk): " + "; ".join(
               f"{k}: W = {n(v.get('W'), 3)}, {pe(v.get('p'))}" for k, v in c["normality"].items()) + ".", "small")]
    return out


def results_section(doc: Document, results: dict | None, figdir: Path | None) -> None:
    doc.h("Results", 1)
    if not results or results["meta"]["status"] != "ok":
        doc.p(PENDING, "pending")
        if results:
            for msg in results["meta"]["messages"]:
                doc.p(msg, "small")
        return
    m = results["meta"]
    for msg in m["messages"]:
        doc.p(msg, "warning")
    doc.h("Data screening and exclusions", 2)
    dq = results["data_quality"]
    cats = dq.get("trial_categories", {})
    doc.p(f"Of {m['n_registered']} registered main-study participants, {m['n_included']} met all inclusion criteria and "
          f"{m['n_excluded']} were excluded. Across main-study experimental trials: {cats.get('correct', 0)} correct, "
          f"{cats.get('incorrect', 0)} incorrect, {cats.get('timeout', 0)} missing responses (timeouts) and "
          f"{cats.get('technically_invalid', 0)} technically invalid trials. Practice trials ({dq.get('n_practice_trials_excluded', 0)}) and "
          f"pilot sessions ({dq.get('n_pilot_sessions_excluded', 0)}) were excluded by design.")
    if results["exclusions"]:
        doc.add(Table(["Participant", "Rule(s)", "Reason(s)"], [[e["participant_id"], ", ".join(e["rules"]), "; ".join(e["reasons"])]
                                                               for e in results["exclusions"]], caption="Excluded participants"))
    doc.h("Descriptive statistics", 2)
    doc.add(_desc_table(results))
    costs = results["descriptives"].get("costs", {})
    if costs:
        doc.add(Table(["Interference cost", "n", "M", "SD", "95% CI"], [[k.replace("_", " "), v.get("n"), n(v.get("mean"), 3), n(v.get("sd"), 3),
                                                                     f"[{n(v.get('ci_low'), 3)}, {n(v.get('ci_high'), 3)}]"] for k, v in costs.items()],
                      caption="Table 5. Interference costs (positive = worse performance than control)"))
    doc.h("Confirmatory analyses", 2)
    doc.add(_confirm_tables(results["confirmatory"]["accuracy"], "Recognition accuracy", 6))
    doc.add(_confirm_tables(results["confirmatory"]["rt"], "Mean correct RT", 7))
    doc.h("Hypothesis outcomes", 2)
    doc.add(Table(["Hypothesis", "Decision", "Evidence"], [[f"**{h['id']}** {h['text']}", h["decision"], h["detail"]] for h in results["hypotheses"]],
                  caption="Table 8. Hypothesis decisions (automatically derived from the pre-specified rules)", widths=[3, 1.4, 2.6]))
    doc.p("A non-significant result does not demonstrate the absence of an effect; it indicates insufficient evidence given this sample.", "note")
    mc = results.get("manipulation_check", {})
    if mc:
        doc.h("Manipulation check: secondary-task performance", 2)
        rows = [[k, n(v["t_test"].get("mean_x"), 3), n(v["t_test"].get("mean_y"), 3), f"{n(v['t_test'].get('t'))} ({v['t_test'].get('df', '—')})",
                 pf(v["t_test"].get("p")), n(v["t_test"].get("cohens_dz")), pf(v["wilcoxon"].get("p"))] for k, v in mc.items()]
        doc.add(Table(["Measure", "Arithmetic (B)", "Symmetry (C)", "t (df)", "p", "d_z", "Wilcoxon p"], rows, caption="Table 9. Secondary-task performance"))
    sens = results.get("sensitivity", {})
    if sens:
        doc.h("Sensitivity analyses", 2)
        rows = []
        for k, v in sens.items():
            if v.get("status") == "ok":
                rows.append([v["dv"], v["omnibus"]["test"], pf(v["omnibus"]["p"])] + [pf(p["p_primary_holm"]) for p in v["pairwise"]])
        doc.add(Table(["Analysis", "Omnibus test", "p", "A vs B (Holm)", "A vs C (Holm)", "B vs C (Holm)"], rows, caption="Table 10. Sensitivity analyses"))
    ex = results.get("exploratory", {})
    if ex:
        doc.h("Exploratory analyses (RQ2)", 2)
        doc.add(Table(["Association", "Method", "r/ρ [95% CI]", "p", "n"],
                      [[c["label"], c.get("method", "—"), f"{n(c.get('r'))} [{n(c.get('ci_low'))}, {n(c.get('ci_high'))}]" if c.get("r") is not None else c.get("note", "—"),
                        pf(c.get("p")), c["n"]] for c in ex.get("correlations", [])], caption="Table 11. Exploratory correlations (no causal interpretation)"))
        for var, lab in (("gender", "Gender"), ("academic_course", "Academic course")):
            dm = ex.get("demographics", {}).get(var)
            if not dm:
                continue
            doc.p(f"**{lab}.** Group sizes: " + ", ".join(f"{k} = {v}" for k, v in dm["counts"].items()) + ". " + dm.get("note", ""))
            for dv, t in dm.get("tests", {}).items():
                if "welch_t" in t:
                    doc.p(f"{dv}: Welch t({n(t['welch_t'].get('df'), 1)}) = {n(t['welch_t'].get('t'))}, {pe(t['welch_t'].get('p'))}, "
                          f"Hedges g = {n(t['welch_t'].get('hedges_g'))}; Mann–Whitney {pe(t['mann_whitney'].get('p'))}.", "small")
                elif "welch_anova" in t:
                    w = t["welch_anova"]; k = t["kruskal_wallis"]
                    doc.p(f"{dv}: Welch F({w.get('df1')}, {n(w.get('df2'), 1)}) = {n(w.get('F'))}, {pe(w.get('p'))}, η² = {n(w.get('eta_sq'), 3)}; "
                          f"Kruskal–Wallis H = {n(k.get('H'))}, {pe(k.get('p'))}.", "small")
        bp = ex.get("block_position")
        if bp:
            fr = bp["accuracy"].get("friedman") or {}
            doc.p("**Order/fatigue.** Mean accuracy by block position: " + ", ".join(
                f"block {k} = {pct(v.get('mean'))}" for k, v in bp["accuracy"]["descriptives"].items()) + f" (Friedman {pe(fr.get('p'))}).")
        ies = ex.get("ies")
        if ies:
            doc.p(f"**Inverse Efficiency Score.** {ies['note']} Available for {ies['n_with_ies']} participant(s): " + ", ".join(
                f"{COND[c]} M = {n(d.get('mean'), 0)} ms" for c, d in ies["descriptives"].items() if d.get("n")) + ".", "small")
    if figdir:
        doc.h("Figures", 2)
        for i, f in enumerate([f for f in results.get("figures", []) if f.get("available")], start=1):
            doc.add(Figure(figdir / f["files"]["png"], f"Figure {i}. {f['title']}" + (f" (N = {f['n']})" if f.get("n") else "")))


def discussion(doc: Document, results: dict | None) -> None:
    doc.h("Discussion", 1)
    if not results or results["meta"]["status"] != "ok":
        doc.p(PENDING, "pending")
        return
    doc.p("AUTO-GENERATED DRAFT: the following interpretation is assembled from the actual statistical results using pre-defined "
          "rules. The authors must review, edit and approve it before submission.", "warning")
    hyp = {h["id"]: h for h in results["hypotheses"]}
    sup = lambda k: hyp.get(k, {}).get("decision") == "supported"  # noqa: E731
    opp = lambda k: "opposite direction" in hyp.get(k, {}).get("decision", "")  # noqa: E731
    doc.h("Were the hypotheses supported?", 2)
    doc.add(Bullets([f"**{h['id']}** — {h['decision']}. {h['detail']}." for h in results["hypotheses"]]))
    doc.h("Possible cognitive explanations", 2)
    if sup("H1") and sup("H2"):
        doc.p("Both secondary tasks reduced recognition accuracy relative to control. This is consistent with accounts in which any "
              "attention-demanding activity during retention reduces the opportunity to maintain the spatial pattern through attentional "
              "refreshing or spatial rehearsal (Barrouillet et al., 2004; Awh et al., 1998).")
    elif sup("H2") and not sup("H1"):
        doc.p("Visual but not numerical interference reduced accuracy relative to control. This pattern is consistent with "
              "domain-specific accounts of working memory, in which a visuospatial secondary task competes for the resources used to "
              "maintain spatial information (Logie et al., 1990; Klauer & Zhao, 2004).")
    elif sup("H1") and not sup("H2"):
        doc.p("Numerical but not visual interference reduced accuracy relative to control — an unexpected pattern that could reflect a "
              "difference in secondary-task difficulty or attentional demand rather than content.")
    else:
        doc.p("Neither secondary task produced a statistically significant reduction in accuracy relative to control. Possible "
              "explanations include genuinely small effects, insufficient power for small-to-medium effects with this sample, "
              "ceiling performance, or secondary tasks that were too easy to disrupt maintenance.")
    if sup("H3"):
        doc.p("Visual interference was more disruptive than numerical interference, which supports the domain-specific prediction "
              "(H3) — provided the two secondary tasks were comparably difficult (see manipulation check).")
    elif opp("H3"):
        doc.p("Numerical interference was more disruptive than visual interference, contrary to H3.")
    else:
        doc.p("There was no statistically significant difference between numerical and visual interference, so the data do not "
              "discriminate clearly between domain-specific and domain-general accounts (cf. Cocchini et al., 2002; Morey & Cowan, 2004).")
    mc = results.get("manipulation_check", {}).get("accuracy", {})
    tt = mc.get("t_test", {}) if mc else {}
    if tt.get("p") is not None:
        doc.p(f"Secondary-task accuracy was {pct(tt.get('mean_x'))} for arithmetic and {pct(tt.get('mean_y'))} for symmetry "
              f"(paired t {pe(tt.get('p'))}). " + ("Because the tasks differed in difficulty, differences between conditions B and C may "
                                                   "reflect difficulty rather than the content of the interference."
                                                   if tt["p"] < 0.05 else "The tasks did not differ significantly in accuracy, although equivalence was not tested."))
    doc.h("Alternative explanations and unexpected findings", 2)
    items = ["Differences between control and interference conditions combine cognitive load with the requirement to make an "
             "additional response; motor/decision demands cannot be separated from interference in this design.",
             "Both tasks share the F/J keys; response carry-over between secondary and recognition responses is possible."]
    cor = [c for c in results.get("exploratory", {}).get("correlations", []) if c["x"] == "overall_accuracy"]
    if cor and cor[0].get("r") is not None:
        r = cor[0]["r"]
        items.append(f"The across-participant association between accuracy and RT was {cor[0]['method']} r = {r:.2f} ({pe(cor[0].get('p'))}); "
                     + ("a positive association (more accurate participants slower) would suggest individual speed–accuracy trade-offs."
                        if r > 0 else "a negative association suggests general ability differences rather than a speed–accuracy trade-off."))
    ceil = results["confirmatory"]["accuracy"].get("ceiling", {})
    if any(v > 0.25 for v in ceil.values()):
        items.append("More than a quarter of participants reached 100% accuracy in at least one condition, indicating a ceiling effect.")
    for k in ("H1", "H2", "H3"):
        if opp(k):
            items.append(f"{k}: a statistically significant effect in the direction opposite to prediction was found and requires explanation.")
    doc.add(Bullets(items))
    doc.h("Comparison with previous literature", 2)
    doc.p("[Authors: compare the observed effect sizes with the studies reviewed (e.g. Logie et al., 1990; Klauer & Zhao, 2004; "
          "Morey & Cowan, 2004; Kane et al., 2004). Do not over-interpret: the sample is small and from a single population.]", "pending")


def limitations(doc: Document, results: dict | None) -> None:
    doc.h("Limitations", 1)
    nn = results["meta"]["n_included"] if results else None
    items = [
        f"**Sample size.** {'N = ' + str(nn) + '. ' if nn else ''}With about 20 participants, a paired comparison has 80% power only for "
        "effects of d_z ≥ 0.66 (α = .05); smaller effects may go undetected and estimates are imprecise.",
        "**Convenience sampling.** University students recruited through personal and class networks; results may not generalise.",
        "**Demographic imbalance.** Gender and course groups are small and unequal, so demographic comparisons are exploratory and often descriptive only.",
        "**Restricted age range.** A narrow student age range limits age-related conclusions.",
        "**Browser and hardware timing.** Browser timing is not laboratory-grade; mitigated by frame-synchronised presentation, measured "
        "durations, a single testing computer and a wired keyboard.",
        "**Secondary-task difficulty differences.** Arithmetic and symmetry tasks may differ in difficulty and attentional demand.",
        "**Construct validity.** Recognition with a whole-display probe may rely on holistic familiarity; the task does not isolate visuospatial "
        "storage from executive control; the control condition has no secondary response.",
        "**Practice effects and fatigue.** Mitigated by counterbalancing and breaks but not eliminated.",
        "**Generalisability.** A single set size, grid and timing configuration; effects may differ with other parameters.",
    ]
    doc.add(Bullets(items))


def conclusion(doc: Document, results: dict | None) -> None:
    doc.h("Conclusion", 1)
    if not results or results["meta"]["status"] != "ok":
        doc.p(PENDING, "pending")
        return
    hyp = results["hypotheses"]
    acc = results["confirmatory"]["accuracy"]
    d = results["descriptives"]["accuracy"]
    doc.p("AUTO-GENERATED DRAFT — review required.", "warning")
    doc.p(f"In {results['meta']['n_included']} university students, mean recognition accuracy was {pct(d['A']['mean'])} without "
          f"interference, {pct(d['B']['mean'])} with numerical interference and {pct(d['C']['mean'])} with visual interference "
          f"(omnibus {pe(acc['omnibus']['p'])}). " + " ".join(f"{h['id']}: {h['decision']}." for h in hyp if h["id"] != "H0")
          + " These conclusions concern associations observed under the specific task parameters used and should be interpreted in light "
            "of the limitations above.")


def references(doc: Document) -> None:
    doc.h("References", 1)
    md = (RESEARCH / "Literature_Review.md").read_text(encoding="utf-8")
    refs = md.split("## References (APA 7)", 1)[1] if "## References (APA 7)" in md else ""
    for line in refs.strip().splitlines():
        if line.strip():
            doc.p(line.strip(), "normal")


def appendices(doc: Document, cfg: ExperimentConfig, results: dict | None, version: str | None) -> None:
    doc.add(PageBreak())
    doc.h("Appendices", 1)
    doc.h("Appendix A. Participant instructions", 2)
    doc.add(_md("Participant_Instructions.md", base_level=3))
    doc.h("Appendix B. Informed consent", 2)
    doc.add(_md("Informed_Consent.md", base_level=3))
    doc.h("Appendix C. Experiment screenshots", 2)
    shots = sorted((REPO_ROOT / "docs" / "screenshots").glob("*.png"))
    if shots:
        for s in shots:
            doc.add(Figure(s, f"Screenshot: {s.stem.replace('_', ' ')}", 0.75))
    else:
        doc.p("[Screenshots not yet captured — run scripts/capture_screenshots.sh]", "pending")
    doc.h("Appendix D. Data dictionary", 2)
    for sheet, vars_ in (("Participants", PARTICIPANT_VARS), ("Contacts (confidential; never reported)", CONTACT_VARS),
                         ("Sessions", SESSION_VARS), ("Raw_Trials", TRIAL_VARS)):
        doc.add(Table(["Variable", "Type", "Unit", "Req.", "Description"], [[v.name, v.type, v.unit, "yes" if v.required else "no", v.description] for v in vars_],
                      caption=sheet, widths=[2, 0.8, 1, 0.5, 4]))
    doc.h("Appendix E. Technical configuration", 2)
    doc.p(f"Experiment version: {version or 'default pre-pilot configuration (not yet locked)'}; configuration hash {cfg.canonical_hash()[:16]}.")
    from .document import Code

    doc.add(Code(json.dumps(cfg.to_json_dict(), indent=2)))
    if results:
        doc.p("Software: " + ", ".join(f"{k} {v}" for k, v in results["meta"]["software"].items()), "small")
    doc.h("Appendix F. Statistical methodology (Statistical Analysis Plan)", 2)
    doc.add(_md("Statistical_Analysis_Plan.md", base_level=3))
    doc.h("Appendix G. Pilot-testing protocol", 2)
    p = REPO_ROOT / "experiment" / "documentation" / "Pilot_Testing_Protocol.md"
    doc.add(from_markdown(p.read_text(encoding="utf-8"), base_level=3))


# ---------------------------------------------------------------------------

def build(cfg: ExperimentConfig, settings: dict, results: dict | None, figdir: Path | None, version: str | None,
          stimdir: Path | None = None) -> tuple[Document, bool]:
    """`stimdir` holds the design figures drawn for this configuration (default: experiment/stimuli)."""
    stimdir = stimdir or REPO_ROOT / "experiment" / "stimuli"
    final = bool(results and results["meta"]["status"] == "ok")
    synthetic = bool(results and any(str(p.get("participant_id", "")).upper().startswith("SYN")
                                     for p in results.get("participant_summary", [])))
    watermark = None if final else "PRELIMINARY — RESULTS PENDING GENUINE DATA"
    if synthetic:
        watermark = "SYNTHETIC TEST DATA — SOFTWARE VERIFICATION ONLY — NOT RESEARCH FINDINGS"
    doc = Document(f"SMIT Research Report — {'SYNTHETIC TEST' if synthetic else 'FINAL' if final else 'PRELIMINARY'}", watermark=watermark)
    title_page(doc, settings, final, results if final else None)
    abstract(doc, cfg, results, final)
    doc.h("Introduction", 1)
    doc.p("Spatial working memory allows us to hold the layout of objects in mind for a few seconds — for example, remembering where "
          "items are on a map or a whiteboard while doing something else. Everyday life rarely allows undisturbed rehearsal: people "
          "calculate, read or look at other displays while trying to remember. Understanding whether different kinds of concurrent "
          "activity disrupt spatial memory equally, or whether disruption depends on overlap in content, informs theories of working "
          "memory (domain-specific versus domain-general resources) and has practical relevance for learning and multitasking.")
    doc.p("This project adapts principles of the visual change-detection and complex-span paradigms into a single task, SMIT, in which a "
          "brief spatial pattern must be maintained across a delay that is empty, filled with arithmetic verification, or filled with a "
          "spatial symmetry judgement. Accuracy and reaction time of the delayed recognition decision are compared across conditions.")
    doc.h("Literature Review", 1)
    doc.add(_md("Literature_Review.md", base_level=2, drop_sections=("References",)))
    doc.h("Theoretical Framework", 1)
    doc.add(_md("Theoretical_Framework.md", base_level=2))
    doc.h("Research Questions and Hypotheses", 1)
    doc.add(_md("Research_Question_and_Hypotheses.md", base_level=2))
    methodology(doc, cfg, settings, results if final else None, stimdir)
    cognitive_task_design(doc)
    pilot_section(doc, settings)
    results_section(doc, results if final else results, figdir if final else None)
    discussion(doc, results if final else None)
    limitations(doc, results if final else None)
    dev = (settings.get("deviations_from_plan") or "").strip()
    doc.h("Deviations from the Analysis Plan", 1)
    doc.p(dev if dev else ("None recorded." if final else "Not applicable before data collection."))
    conclusion(doc, results if final else None)
    references(doc)
    appendices(doc, cfg, results if final else None, version)
    return doc, final
