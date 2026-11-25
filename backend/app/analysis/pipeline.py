"""End-to-end analysis pipeline implementing the Statistical Analysis Plan.

Data (collected or imported) -> cleaning & classification -> pre-specified
exclusions -> descriptives -> confirmatory tests (H0–H4) -> exploratory analyses
-> figures -> JSON results stored in ``analysis_runs``.

Nothing here contains a hard-coded result: every number and decision is derived
from the data at run time. If data are insufficient, results are marked as such.
"""
from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..experiment.config import AnalysisConfig, ExperimentConfig
from ..models import AnalysisRun, ExperimentConfigVersion
from ..services.dataset import dataset_hash, load_frames
from ..settings import get_settings
from . import stats as S
from .metrics import COND_LABELS, COND_NAMES, classify_trials, participant_condition_metrics, wide_summary

PAIRS = [("A", "B", "H1"), ("A", "C", "H2"), ("B", "C", "H3")]
MIN_N_INFERENCE = 3


def _software() -> dict:
    import matplotlib
    import pingouin
    import scipy
    import statsmodels

    return {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__,
            "scipy": scipy.__version__, "statsmodels": statsmodels.__version__, "pingouin": pingouin.__version__,
            "matplotlib": matplotlib.__version__}


def _analysis_config(db: Session, versions: list[str]) -> tuple[AnalysisConfig, int, ExperimentConfig]:
    """Use the analysis thresholds of the (single) locked configuration used by the data."""
    cfgs = []
    for v in versions:
        row = db.scalar(select(ExperimentConfigVersion).where(ExperimentConfigVersion.experiment_version == v))
        if row:
            cfgs.append(ExperimentConfig.model_validate(row.config_json))
    if not cfgs:
        active = db.scalar(select(ExperimentConfigVersion).where(ExperimentConfigVersion.is_active_main))
        cfgs = [ExperimentConfig.model_validate(active.config_json)] if active else [ExperimentConfig()]
    c = cfgs[0]
    return c.analysis, c.grid.highlight_count, c


def _clean(v):
    if isinstance(v, (np.floating, float)):
        return None if (np.isnan(v) or np.isinf(v)) else float(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, dict):
        return {str(k): _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.isoformat()
    return v


# ---------------------------------------------------------------------------
# Build participant table
# ---------------------------------------------------------------------------

def build_participant_table(frames: dict[str, pd.DataFrame], acfg: AnalysisConfig, n_items: int) -> dict:
    parts, sessions, trials, summ = frames["participants"], frames["sessions"], frames["trials"], frames["imported_summaries"]
    msgs: list[str] = []
    # sessions: main study only
    sess = sessions[sessions["session_type"] == "main"].copy()
    completed = sess[sess["completion_status"] == "completed"]
    multi = completed.groupby("participant_id").size()
    if (multi > 1).any():
        msgs.append(f"{int((multi > 1).sum())} participant(s) have more than one completed session; only the first is analysed.")
    first_completed = completed.sort_values("start_time", na_position="last").groupby("participant_id").head(1)
    use_sessions = set(first_completed["session_id"])
    t = trials[trials["session_id"].isin(sess["session_id"])].copy()
    ct_all = classify_trials(t, acfg)
    ct = ct_all[ct_all["session_id"].isin(use_sessions)]
    pcm = participant_condition_metrics(ct, n_items) if len(ct) else pd.DataFrame()
    wide = wide_summary(pcm, ct, acfg.ies_min_accuracy) if len(pcm) else pd.DataFrame(columns=["participant_id"])
    # add block-position info
    order_map = sess.set_index("session_id")["condition_order"].to_dict()

    rows = []
    trial_pids = set(sess["participant_id"])
    for _, p in parts.iterrows():
        pid = p["participant_id"]
        reasons, rules = [], []
        has_summary = pid in set(summ["participant_id"])
        if p["status"] != "active":
            reasons.append(f"participant {p['status']}: {p['status_reason'] or 'no reason recorded'}")
            rules.append("status")
        w = wide[wide["participant_id"] == pid]
        row = {"participant_id": pid, "age": p["age"], "gender": p["gender"], "academic_course": p["academic_course"],
               "data_source": p["data_source"], "summary_only": bool(has_summary and pid not in trial_pids)}
        if len(w):
            row.update(w.iloc[0].to_dict())
            sid = first_completed.loc[first_completed["participant_id"] == pid, "session_id"]
            row["condition_order"] = order_map.get(sid.iloc[0]) if len(sid) else None
            row["experiment_version"] = (sess.loc[sess["session_id"] == sid.iloc[0], "experiment_version"].iloc[0]
                                         if len(sid) else None)
            for c, nm in COND_NAMES.items():
                nv = row.get(f"{nm}_n_valid")
                if nv is None or pd.isna(nv) or nv < acfg.min_valid_trials_per_condition:
                    reasons.append(f"fewer than {acfg.min_valid_trials_per_condition} valid trials in condition {c} ({0 if nv is None or pd.isna(nv) else int(nv)})")
                    rules.append("R2")
            if row.get("timeout_rate") is not None and row["timeout_rate"] > acfg.max_timeout_rate:
                reasons.append(f"timeout rate {row['timeout_rate']:.0%} > {acfg.max_timeout_rate:.0%}")
                rules.append("R3")
            skp = row.get("same_key_proportion")
            if skp is not None and not pd.isna(skp) and skp >= acfg.max_same_key_proportion:
                reasons.append(f"same key on {skp:.0%} of answered trials (≥ {acfg.max_same_key_proportion:.0%})")
                rules.append("R4")
            for nm in ("numerical", "visual"):
                sa = row.get(f"{nm}_secondary_accuracy")
                if sa is not None and not pd.isna(sa) and sa < acfg.min_secondary_accuracy:
                    reasons.append(f"{nm} secondary-task accuracy {sa:.0%} < {acfg.min_secondary_accuracy:.0%}")
                    rules.append("R5")
        elif has_summary:
            s = summ[summ["participant_id"] == pid].iloc[0]
            row.update({"control_accuracy": s["control_accuracy"], "numerical_accuracy": s["numerical_accuracy"],
                        "visual_accuracy": s["visual_accuracy"], "control_mean_correct_rt_ms": s["control_mean_correct_rt_ms"],
                        "numerical_mean_correct_rt_ms": s["numerical_mean_correct_rt_ms"],
                        "visual_mean_correct_rt_ms": s["visual_mean_correct_rt_ms"], "timeout_rate": s["timeout_rate"],
                        "numerical_secondary_accuracy": s["numerical_secondary_accuracy"],
                        "visual_secondary_accuracy": s["visual_secondary_accuracy"],
                        "condition_order": s["condition_order"], "experiment_version": s["experiment_version"]})
            accs = [row["control_accuracy"], row["numerical_accuracy"], row["visual_accuracy"]]
            row["overall_accuracy"] = float(np.mean(accs))
            rts = [row[f"{n}_mean_correct_rt_ms"] for n in COND_NAMES.values()]
            row["overall_mean_correct_rt_ms"] = float(np.nanmean(rts)) if any(r is not None and not pd.isna(r) for r in rts) else None
            row["numerical_accuracy_cost"] = row["control_accuracy"] - row["numerical_accuracy"]
            row["visual_accuracy_cost"] = row["control_accuracy"] - row["visual_accuracy"]
            for nm in ("numerical", "visual"):
                a, b = row[f"{nm}_mean_correct_rt_ms"], row["control_mean_correct_rt_ms"]
                row[f"{nm}_rt_cost_ms"] = None if a is None or b is None or pd.isna(a) or pd.isna(b) else a - b
            row["mean_accuracy_cost"] = np.mean([row["numerical_accuracy_cost"], row["visual_accuracy_cost"]])
            rc = [x for x in (row["numerical_rt_cost_ms"], row["visual_rt_cost_ms"]) if x is not None]
            row["mean_rt_cost_ms"] = float(np.mean(rc)) if rc else None
            if row.get("timeout_rate") is not None and not pd.isna(row["timeout_rate"]) and row["timeout_rate"] > acfg.max_timeout_rate:
                reasons.append("timeout rate above threshold"); rules.append("R3")
            for nm in ("numerical", "visual"):
                sa = row.get(f"{nm}_secondary_accuracy")
                if sa is not None and not pd.isna(sa) and sa < acfg.min_secondary_accuracy:
                    reasons.append(f"{nm} secondary-task accuracy below threshold"); rules.append("R5")
        else:
            reasons.append("no completed main-study session (incomplete, abandoned or withdrawn)")
            rules.append("R1")
        row["excluded"] = bool(reasons)
        row["exclusion_reasons"] = reasons
        row["exclusion_rules"] = sorted(set(rules))
        row["engagement_only_exclusion"] = bool(rules) and set(rules) <= {"R3", "R4", "R5"}
        rows.append(row)
    table = pd.DataFrame(rows)
    return {"table": table, "classified": ct, "classified_all": ct_all, "pcm": pcm, "messages": msgs,
            "sessions": sess}


# ---------------------------------------------------------------------------
# Confirmatory analysis for one DV
# ---------------------------------------------------------------------------

def confirmatory(table: pd.DataFrame, cols: dict[str, str], acfg: AnalysisConfig, dv_label: str,
                 ceiling_check: bool) -> dict:
    wide = table[[cols["A"], cols["B"], cols["C"]]].apply(pd.to_numeric, errors="coerce")
    wide.columns = ["A", "B", "C"]
    complete = wide.dropna()
    n = len(complete)
    res: dict = {"dv": dv_label, "n_complete": n, "n_missing": int(len(wide) - n),
                 "descriptives": {c: S.describe(complete[c]) for c in "ABC"}}
    if n < MIN_N_INFERENCE:
        res["status"] = "insufficient"
        res["note"] = f"Only {n} participant(s) with complete data; at least {MIN_N_INFERENCE} are needed for inferential tests."
        return res
    normality = {f"{a}-{b}": S.shapiro(complete[a] - complete[b]) for a, b, _ in PAIRS}
    violated = [k for k, v in normality.items() if v.get("p") is not None and v["p"] < acfg.normality_alpha]
    undefined = [k for k, v in normality.items() if v.get("p") is None]
    ceiling = {c: float((complete[c] >= 0.999999).mean()) for c in "ABC"} if ceiling_check else {}
    ceiling_problem = [c for c, v in ceiling.items() if v > 0.25]
    if violated or ceiling_problem or undefined:
        route = "nonparametric"
        why = []
        if violated:
            why.append(f"Shapiro–Wilk rejected normality of the paired differences {', '.join(violated)} (p < {acfg.normality_alpha})")
        if undefined:
            why.append(f"normality could not be assessed for {', '.join(undefined)} (no variance)")
        if ceiling_problem:
            why.append(f"more than 25% of participants at 100% accuracy in condition(s) {', '.join(ceiling_problem)}")
        reason = "; ".join(why) + " → Friedman test and Wilcoxon signed-rank tests are primary."
    else:
        route = "parametric"
        reason = ("All paired differences were consistent with normality (Shapiro–Wilk p ≥ "
                  f"{acfg.normality_alpha}) and no ceiling problem was detected → repeated-measures ANOVA and paired t-tests are primary.")
    anova = S.rm_anova(complete)
    fried = S.friedman(complete)
    pairs = []
    for a, b, h in PAIRS:
        pairs.append({"pair": f"{a} vs {b}", "a": a, "b": b, "hypothesis": h,
                      "label": f"{COND_LABELS[a]} vs {COND_LABELS[b]}",
                      "t_test": S.paired_t(complete[a], complete[b]), "wilcoxon": S.wilcoxon(complete[a], complete[b])})
    pt = S.holm([p["t_test"].get("p") for p in pairs])
    pw = S.holm([p["wilcoxon"].get("p") for p in pairs])
    for p, a, b in zip(pairs, pt, pw):
        p["t_test"]["p_holm"] = a
        p["wilcoxon"]["p_holm"] = b
        p["primary"] = "t_test" if route == "parametric" else "wilcoxon"
        p["p_primary_holm"] = a if route == "parametric" else b
        p["significant"] = p["p_primary_holm"] is not None and p["p_primary_holm"] < acfg.alpha
        p["direction"] = ("a > b" if (complete[p["a"]].mean() > complete[p["b"]].mean()) else
                          "a < b" if complete[p["a"]].mean() < complete[p["b"]].mean() else "equal")
    if route == "parametric":
        use_gg = anova.get("sphericity_violated", False)
        omni_p = anova.get("p_gg") if use_gg else anova.get("p")
        omni = {"test": "repeated-measures ANOVA" + (" (Greenhouse–Geisser corrected)" if use_gg else ""), "p": omni_p}
    else:
        omni = {"test": "Friedman test", "p": fried.get("p")}
    omni["significant"] = omni["p"] is not None and omni["p"] < acfg.alpha
    res.update({"status": "ok", "route": route, "route_reason": reason, "normality": normality, "ceiling": ceiling,
                "rm_anova": anova, "friedman": fried, "omnibus": omni, "pairwise": pairs})
    return res


def hypothesis_decisions(acc: dict, rt: dict, alpha: float) -> list[dict]:
    texts = {
        "H1": "Numerical interference reduces recognition accuracy relative to the control condition.",
        "H2": "Visual interference reduces recognition accuracy relative to the control condition.",
        "H3": "Visual interference produces greater spatial memory disruption than numerical interference.",
        "H4": "Interference affects recognition reaction time.",
        "H0": "Interference type has no effect on spatial memory recognition performance (omnibus, accuracy).",
    }
    out = []
    if acc.get("status") != "ok":
        for h in ("H0", "H1", "H2", "H3"):
            out.append({"id": h, "text": texts[h], "decision": "not tested", "detail": acc.get("note", "insufficient data")})
    else:
        om = acc["omnibus"]
        out.append({"id": "H0", "text": texts["H0"],
                    "decision": "rejected" if om["significant"] else "not rejected",
                    "detail": f"{om['test']}: p {_pfmt(om['p'])}"})
        for p in acc["pairwise"]:
            h = p["hypothesis"]
            expected = "a > b"  # control > numerical, control > visual, numerical > visual
            if not p["significant"]:
                dec = "not supported (no statistically significant difference)"
            elif p["direction"] == expected:
                dec = "supported"
            else:
                dec = "not supported (significant effect in the opposite direction)"
            test = p[p["primary"]]
            es = (f"d_z = {test.get('cohens_dz'):.2f}" if p["primary"] == "t_test" and test.get("cohens_dz") is not None
                  else f"r_rb = {test.get('rank_biserial'):.2f}" if test.get("rank_biserial") is not None else "")
            out.append({"id": h, "text": texts[h], "decision": dec,
                        "detail": f"{p['label']}: {test['test']}, Holm-adjusted p {_pfmt(p['p_primary_holm'])}{', ' + es if es else ''}"})
    if rt.get("status") != "ok":
        out.append({"id": "H4", "text": texts["H4"], "decision": "not tested", "detail": rt.get("note", "insufficient data")})
    else:
        om = rt["omnibus"]
        out.append({"id": "H4", "text": texts["H4"], "decision": "supported" if om["significant"] else
                    "not supported (no statistically significant effect)", "detail": f"{om['test']} on mean correct RT: p {_pfmt(om['p'])}"})
    order = ["H0", "H1", "H2", "H3", "H4"]
    return sorted(out, key=lambda x: order.index(x["id"]))


def _pfmt(p) -> str:
    """APA-style p-value including the relation sign, e.g. '= .042' or '< .001'."""
    if p is None:
        return "= n/a"
    if p < 0.001:
        return "< .001"
    return "= " + (f"{p:.3f}".lstrip("0") if p < 1 else "1.000")


# ---------------------------------------------------------------------------
# Exploratory
# ---------------------------------------------------------------------------

def exploratory(inc: pd.DataFrame, ct: pd.DataFrame, acfg: AnalysisConfig, sessions: pd.DataFrame) -> dict:
    out: dict = {}
    pairs = [("age", "overall_accuracy", "Age vs overall accuracy"),
             ("age", "overall_mean_correct_rt_ms", "Age vs overall mean correct RT"),
             ("age", "mean_accuracy_cost", "Age vs mean accuracy interference cost"),
             ("age", "mean_rt_cost_ms", "Age vs mean RT interference cost"),
             ("overall_accuracy", "overall_mean_correct_rt_ms", "Overall accuracy vs overall mean correct RT (speed–accuracy)")]
    out["correlations"] = [{"x": x, "y": y, "label": lab, **S.correlation(inc.get(x), inc.get(y), acfg.normality_alpha)}
                           for x, y, lab in pairs if x in inc and y in inc]
    num_cols = [c for c in ["age", "control_accuracy", "numerical_accuracy", "visual_accuracy", "control_mean_correct_rt_ms",
                            "numerical_mean_correct_rt_ms", "visual_mean_correct_rt_ms", "numerical_accuracy_cost",
                            "visual_accuracy_cost", "numerical_rt_cost_ms", "visual_rt_cost_ms", "overall_accuracy",
                            "overall_mean_correct_rt_ms", "timeout_rate"] if c in inc]
    mat = inc[num_cols].apply(pd.to_numeric, errors="coerce")
    usable = [c for c in num_cols if mat[c].notna().sum() >= 4 and mat[c].nunique() > 1]
    out["correlation_matrix"] = ({"variables": usable, "method": "spearman",
                                  "r": mat[usable].corr(method="spearman").round(4).values.tolist()} if len(usable) >= 2 else None)

    # demographic groups
    demo = {}
    for var in ("gender", "academic_course"):
        res = {"groups": {}, "tests": {}}
        g = inc[[var, "overall_accuracy", "overall_mean_correct_rt_ms", "mean_accuracy_cost"]].copy()
        g[var] = g[var].fillna("Missing")
        counts = g[var].value_counts()
        res["counts"] = counts.to_dict()
        for dv in ("overall_accuracy", "overall_mean_correct_rt_ms", "mean_accuracy_cost"):
            res["groups"][dv] = {k: S.describe(v[dv]) for k, v in g.groupby(var)}
        eligible = [k for k, n in counts.items() if n >= acfg.min_group_size_for_inference
                    and k not in ("Missing", "Prefer not to answer")]
        res["eligible_groups"] = eligible
        if len(eligible) < 2:
            res["note"] = (f"Inferential comparison not performed: fewer than two groups with at least "
                           f"{acfg.min_group_size_for_inference} participants (descriptive statistics only).")
        else:
            for dv in ("overall_accuracy", "overall_mean_correct_rt_ms", "mean_accuracy_cost"):
                groups = {k: g.loc[g[var] == k, dv] for k in eligible}
                res["tests"][dv] = (S.two_groups(groups[eligible[0]], groups[eligible[1]], (eligible[0], eligible[1]))
                                    if len(eligible) == 2 else S.multi_groups(groups))
            small = [k for k in counts.index if k not in eligible]
            if small:
                res["note"] = f"Groups excluded from inference (n < {acfg.min_group_size_for_inference} or undisclosed): {', '.join(map(str, small))}."
        demo[var] = res
    out["demographics"] = demo

    # block position (order/fatigue) and trial trends — trial-level data only
    if len(ct):
        inc_ids = set(inc["participant_id"])
        v = ct[ct["valid"] & ct["participant_id"].isin(inc_ids)].copy()
        if len(v):
            bp = v.groupby(["participant_id", "block_number"]).agg(acc=("correct", "mean")).reset_index()
            bp_rt = v[v["rt_valid"]].groupby(["participant_id", "block_number"])["reaction_time_ms"].mean().reset_index()
            wa = bp.pivot(index="participant_id", columns="block_number", values="acc").dropna()
            wr = bp_rt.pivot(index="participant_id", columns="block_number", values="reaction_time_ms").dropna()
            out["block_position"] = {
                "accuracy": {"descriptives": {int(c): S.describe(wa[c]) for c in wa.columns},
                             "rm_anova": S.rm_anova(wa) if wa.shape[1] == 3 else None,
                             "friedman": S.friedman(wa) if wa.shape[1] == 3 else None},
                "rt": {"descriptives": {int(c): S.describe(wr[c]) for c in wr.columns},
                       "rm_anova": S.rm_anova(wr) if wr.shape[1] == 3 else None,
                       "friedman": S.friedman(wr) if wr.shape[1] == 3 else None},
            }
            v["trial_in_block"] = v.groupby(["session_id", "block_number"]).cumcount() + 1
            tb = v.groupby("trial_in_block").agg(accuracy=("correct", "mean"), n=("correct", "size")).reset_index()
            out["trial_trend"] = tb.to_dict(orient="records")
    # condition order (descriptive)
    if "condition_order" in inc:
        co = inc.groupby("condition_order").agg(n=("participant_id", "size"), overall_accuracy=("overall_accuracy", "mean"),
                                                mean_accuracy_cost=("mean_accuracy_cost", "mean")).reset_index()
        out["condition_order"] = co.to_dict(orient="records")
    # IES
    ies_cols = [f"{n}_ies" for n in COND_NAMES.values()]
    if all(c in inc for c in ies_cols):
        ies = inc[ies_cols].apply(pd.to_numeric, errors="coerce")
        n_ok = int(ies.dropna().shape[0])
        out["ies"] = {"n_with_ies": n_ok, "n_without": int(len(inc) - n_ok),
                      "descriptives": {c: S.describe(ies[f"{n}_ies"]) for c, n in COND_NAMES.items()},
                      "note": ("IES computed only for participants with accuracy ≥ "
                               f"{acfg.ies_min_accuracy:.0%} in every condition (Bruyer & Brysbaert, 2011); supplementary, not confirmatory.")}
    return out


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def data_quality(frames: dict, built: dict) -> dict:
    t = frames["trials"]
    sess = built["sessions"]
    ct_all = built["classified_all"]
    main_t = t[t["session_id"].isin(sess["session_id"])]
    exp_t = main_t[~main_t["practice_trial"].astype(bool)] if len(main_t) else main_t
    q: dict = {
        "sessions_by_status": sess["completion_status"].value_counts().to_dict(),
        "n_main_sessions": int(len(sess)),
        "n_experimental_trials": int(len(exp_t)),
        "n_practice_trials_excluded": int(len(main_t) - len(exp_t)),
        "n_pilot_sessions_excluded": int((frames["sessions"]["session_type"] == "pilot").sum()),
    }
    if len(ct_all):
        q["trial_categories"] = ct_all["category"].value_counts().to_dict()
        q["timing_flags"] = ct_all["timing_quality_flag"].fillna("ok").value_counts().to_dict()
        q["focus_loss_trials"] = int(ct_all["focus_loss"].astype(bool).sum()) if "focus_loss" in ct_all else 0
        q["anticipatory_responses"] = int(ct_all["anticipatory"].sum())
        q["researcher_excluded_trials"] = int(ct_all["exclusion_status"].eq("excluded").sum())
        dev = {}
        for name, pk, mk in (("fixation", "planned_fixation_duration_ms", "actual_fixation_duration_ms"),
                             ("memory_stimulus", "planned_stimulus_duration_ms", "measured_stimulus_duration_ms"),
                             ("interference", "planned_interference_duration_ms", "measured_interference_duration_ms"),
                             ("retention", "planned_retention_duration_ms", "measured_retention_duration_ms")):
            d = (pd.to_numeric(ct_all[mk], errors="coerce") - pd.to_numeric(ct_all[pk], errors="coerce")).dropna()
            dev[name] = {**S.describe(d), "n_measured": int(len(d)), "n_missing": int(len(ct_all) - len(d))}
        q["timing_deviation_ms"] = dev
        rr = pd.to_numeric(sess["estimated_refresh_rate"], errors="coerce").dropna()
        q["refresh_rates_hz"] = rr.round(1).value_counts().to_dict()
        key = ["session_id", "practice_trial", "practice_attempt", "trial_number"]
        q["duplicate_trials"] = int(t.duplicated(subset=[k for k in key if k in t]).sum())
        miss_cols = ["participant_response", "reaction_time_ms", "measured_stimulus_duration_ms", "interference_response"]
        q["missing_values"] = {c: int(ct_all[c].isna().sum()) for c in miss_cols if c in ct_all}
        sec = ct_all[ct_all["condition"].isin(["B", "C"])]
        if len(sec):
            q["secondary_no_response"] = int(sec["interference_response"].isna().sum())
    return q


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

def run_analysis(db: Session, out_dir: Path | None = None, make_figures: bool = True) -> dict:
    frames = load_frames(db, "main")
    versions = sorted(v for v in set(frames["sessions"]["experiment_version"].dropna()) |
                      set(frames["imported_summaries"]["experiment_version"].dropna()))
    acfg, n_items, cfg = _analysis_config(db, versions)
    built = build_participant_table(frames, acfg, n_items)
    table: pd.DataFrame = built["table"]
    messages = list(built["messages"])
    if len(versions) > 1:
        messages.append(f"Data come from {len(versions)} experiment versions ({', '.join(versions)}). "
                        "Pooled analysis shown; check that versions differ only in documented ways.")
    inc = table[~table["excluded"]].copy() if len(table) else table
    n_inc = int(len(inc))
    status = "ok" if n_inc >= MIN_N_INFERENCE else ("no_data" if n_inc == 0 else "insufficient")
    if status != "ok":
        messages.append(f"Only {n_inc} eligible participant(s); inferential statistics require at least {MIN_N_INFERENCE} "
                        "(and the study target is 20). Results are pending genuine data.")
    elif n_inc < 20:
        messages.append(f"{n_inc} eligible participants — below the study target of 20. Interpret with caution.")

    acc_cols = {"A": "control_accuracy", "B": "numerical_accuracy", "C": "visual_accuracy"}
    rt_cols = {"A": "control_mean_correct_rt_ms", "B": "numerical_mean_correct_rt_ms", "C": "visual_mean_correct_rt_ms"}
    results: dict = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(), "dataset_hash": dataset_hash(frames),
            "status": status, "n_registered": int(len(frames["participants"])), "n_analysed_candidates": int(len(table)),
            "n_included": n_inc, "n_excluded": int(table["excluded"].sum()) if len(table) else 0,
            "n_summary_only": int(table["summary_only"].sum()) if len(table) else 0,
            "experiment_versions": versions, "analysis_config": acfg.model_dump(), "software": _software(),
            "messages": messages, "target_n": 20,
        },
        "data_quality": data_quality(frames, built),
        "exclusions": [{"participant_id": r["participant_id"], "rules": r["exclusion_rules"], "reasons": r["exclusion_reasons"]}
                       for _, r in table.iterrows() if r["excluded"]] if len(table) else [],
    }
    if n_inc:
        results["sample"] = {
            "n": n_inc, "age": S.describe(inc["age"]),
            "gender": inc["gender"].fillna("Missing").value_counts().to_dict(),
            "academic_course": inc["academic_course"].fillna("Missing").value_counts().to_dict(),
            "condition_order": inc["condition_order"].fillna("Unknown").value_counts().to_dict() if "condition_order" in inc else {},
        }
        desc = {}
        for label, cols in (("accuracy", acc_cols), ("mean_correct_rt_ms", rt_cols)):
            desc[label] = {c: S.describe(inc[col]) for c, col in cols.items() if col in inc}
        for nm, c in (("timeout_rate", "timeout_rate"), ("median_correct_rt_ms", "median_correct_rt_ms"),
                      ("dprime", "dprime"), ("k_pashler", "k"), ("accuracy_answered", "accuracy_answered")):
            cols = {k: f"{v}_{c}" for k, v in COND_NAMES.items()}
            if all(col in inc for col in cols.values()):
                desc[nm] = {k: S.describe(inc[col]) for k, col in cols.items()}
        desc["costs"] = {c: S.describe(inc[c]) for c in ("numerical_accuracy_cost", "visual_accuracy_cost",
                                                         "numerical_rt_cost_ms", "visual_rt_cost_ms") if c in inc}
        desc["overall"] = {c: S.describe(inc[c]) for c in ("overall_accuracy", "overall_mean_correct_rt_ms", "timeout_rate") if c in inc}
        desc["secondary"] = {c: S.describe(inc[c]) for c in ("numerical_secondary_accuracy", "visual_secondary_accuracy",
                                                             "numerical_secondary_mean_rt_ms", "visual_secondary_mean_rt_ms") if c in inc}
        ct = built["classified"]
        if len(ct):
            v = ct[ct["participant_id"].isin(inc["participant_id"])]
            tl = {}
            for c in "ABC":
                g = v[(v["condition"] == c)]
                gv = g[g["valid"]]
                rts = gv.loc[gv["rt_valid"], "reaction_time_ms"]
                tl[c] = {"n_trials": int(len(g)), "n_valid": int(len(gv)), "accuracy": S._f(gv["correct"].mean()),
                         "error_rate": S._f(1 - gv["correct"].mean()), "timeout_rate": S._f(gv["timeout"].mean()),
                         "mean_correct_rt": S._f(rts.mean()), "median_correct_rt": S._f(rts.median())}
            desc["trial_level"] = tl
        results["descriptives"] = desc
    if status == "ok":
        acc = confirmatory(inc, acc_cols, acfg, "Recognition accuracy (proportion correct)", ceiling_check=True)
        rt = confirmatory(inc, rt_cols, acfg, "Mean correct recognition RT (ms)", ceiling_check=False)
        results["confirmatory"] = {"accuracy": acc, "rt": rt}
        results["hypotheses"] = hypothesis_decisions(acc, rt, acfg.alpha)
        sec_b, sec_c = "numerical_secondary_accuracy", "visual_secondary_accuracy"
        mc = {}
        if sec_b in inc and sec_c in inc:
            d = inc[[sec_b, sec_c]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(d) >= MIN_N_INFERENCE:
                mc["accuracy"] = {"t_test": S.paired_t(d[sec_b], d[sec_c]), "wilcoxon": S.wilcoxon(d[sec_b], d[sec_c]),
                                  "normality": S.shapiro(d[sec_b] - d[sec_c])}
        rb, rc = "numerical_secondary_mean_rt_ms", "visual_secondary_mean_rt_ms"
        if rb in inc and rc in inc:
            d = inc[[rb, rc]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(d) >= MIN_N_INFERENCE:
                mc["rt"] = {"t_test": S.paired_t(d[rb], d[rc]), "wilcoxon": S.wilcoxon(d[rb], d[rc]),
                            "normality": S.shapiro(d[rb] - d[rc])}
        results["manipulation_check"] = mc
        sens = {}
        ans_cols = {k: f"{v}_accuracy_answered" for k, v in COND_NAMES.items()}
        if all(c in inc for c in ans_cols.values()):
            sens["accuracy_answered_only"] = confirmatory(inc, ans_cols, acfg, "Accuracy (answered trials only)", True)
        eng = table[(~table["excluded"]) | (table["engagement_only_exclusion"])]
        if len(eng) > n_inc:
            sens["including_engagement_exclusions"] = confirmatory(eng, acc_cols, acfg, "Accuracy incl. engagement-flagged participants", True)
        dp = {k: f"{v}_dprime" for k, v in COND_NAMES.items()}
        if all(c in inc for c in dp.values()):
            sens["dprime"] = confirmatory(inc, dp, acfg, "d′ (sensitivity)", False)
        results["sensitivity"] = sens
        results["exploratory"] = exploratory(inc, built["classified"], acfg, built["sessions"])
    # de-identified participant table (no emails exist in these frames)
    keep = [c for c in table.columns if c not in ("exclusion_reasons",)] if len(table) else []
    results["participant_summary"] = json.loads(table[keep].to_json(orient="records")) if len(table) else []
    results["figures"] = []
    if make_figures and out_dir is not None and n_inc > 0:
        from .figures import make_all

        results["figures"] = make_all(out_dir, inc, built["classified"], results, frames)
    return _clean(results)


def run_and_store(db: Session) -> AnalysisRun:
    run = AnalysisRun(status="running", dataset_hash="pending")
    db.add(run)
    db.flush()
    out_dir = get_settings().outputs_dir / "analysis" / f"run_{run.id:04d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        res = run_analysis(db, out_dir)
        run.status = "completed"
        run.results_json = res
        run.dataset_hash = res["meta"]["dataset_hash"]
        run.n_participants_included = res["meta"]["n_included"]
        run.n_participants_total = res["meta"]["n_registered"]
        run.experiment_versions = res["meta"]["experiment_versions"]
        run.software_versions = res["meta"]["software"]
        run.output_dir = str(out_dir)
        (out_dir / "results.json").write_text(json.dumps(res, indent=2, default=str))
    except Exception as exc:
        run.status = "failed"
        run.error = f"{type(exc).__name__}: {exc}"
        db.commit()
        raise
    from ..services.audit import audit

    audit(db, "analysis_run", entity_type="analysis", entity_id=str(run.id),
          details={"n_included": run.n_participants_included, "dataset_hash": run.dataset_hash[:12]})
    db.commit()
    return run
