"""Trial classification and participant-level metrics (Statistical Analysis Plan §3 and §5).

Pure pandas/numpy; used by the analysis pipeline, the import preview and the
Participant_Summary sheet of exported workbooks.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from ..experiment.config import AnalysisConfig

COND_NAMES = {"A": "control", "B": "numerical", "C": "visual"}
COND_LABELS = {"A": "Control", "B": "Numerical interference", "C": "Visual interference"}


def _bool(s: pd.Series) -> pd.Series:
    def conv(v):
        if isinstance(v, (bool, np.bool_)):
            return bool(v)
        if v is None or (isinstance(v, float) and np.isnan(v)):
            return False
        return str(v).strip().lower() in ("true", "1", "yes")
    return s.map(conv).astype(bool)


def classify_trials(trials: pd.DataFrame, acfg: AnalysisConfig) -> pd.DataFrame:
    """Add classification columns to experimental (non-practice) trials.

    category: technically_invalid | timeout | incorrect | correct
    """
    t = trials.copy()
    if t.empty:
        for c in ("valid", "timeout", "answered", "correct", "anticipatory", "rt_valid", "category"):
            t[c] = pd.Series(dtype=object)
        return t
    t["practice_trial"] = _bool(t["practice_trial"])
    t = t[~t["practice_trial"]].copy()
    t["reaction_time_ms"] = pd.to_numeric(t["reaction_time_ms"], errors="coerce")
    t["interference_reaction_time_ms"] = pd.to_numeric(t.get("interference_reaction_time_ms"), errors="coerce")
    excluded = t["exclusion_status"].fillna("included").eq("excluded")
    invalid_timing = t["timing_quality_flag"].fillna("ok").eq("invalid")
    t["valid"] = ~(excluded | invalid_timing)
    resp = t["participant_response"].where(t["participant_response"].isin(["same", "different"]))
    t["participant_response"] = resp
    t["timeout"] = resp.isna()
    t["answered"] = ~t["timeout"]
    t["correct"] = (resp == t["correct_answer"]) & t["answered"]
    t["anticipatory"] = t["answered"] & (t["reaction_time_ms"] < acfg.min_valid_rt_ms)
    t["rt_valid"] = t["valid"] & t["correct"] & ~t["anticipatory"] & t["reaction_time_ms"].notna()
    t["category"] = np.select(
        [~t["valid"], t["timeout"], ~t["correct"]], ["technically_invalid", "timeout", "incorrect"], "correct")
    if "interference_response" in t:
        ir = t["interference_response"].where(t["interference_response"].isin(["true", "false"]))
        t["interference_response"] = ir
        t["sec_correct"] = (ir == t["interference_correct_answer"]) & ir.notna()
    return t


def dprime_loglinear(hits: int, n_signal: int, fas: int, n_noise: int) -> float:
    """d' with the log-linear correction (Hautus, 1995)."""
    if n_signal == 0 or n_noise == 0:
        return float("nan")
    h = (hits + 0.5) / (n_signal + 1)
    f = (fas + 0.5) / (n_noise + 1)
    return float(stats.norm.ppf(h) - stats.norm.ppf(f))


def pashler_k(hit: float, fa: float, n_items: int) -> float:
    if np.isnan(hit) or np.isnan(fa) or fa >= 1:
        return float("nan")
    return float(n_items * (hit - fa) / (1 - fa))


def participant_condition_metrics(ct: pd.DataFrame, n_items: int = 4) -> pd.DataFrame:
    """One row per participant × condition from classified trials (valid trials only)."""
    rows = []
    for (pid, cond), g in ct.groupby(["participant_id", "condition"], sort=True):
        v = g[g["valid"]]
        n = len(v)
        n_ans = int(v["answered"].sum())
        diff = v[v["correct_answer"] == "different"]
        same = v[v["correct_answer"] == "same"]
        hits = int((diff["participant_response"] == "different").sum())
        fas = int((same["participant_response"] == "different").sum())
        hit_rate = hits / len(diff) if len(diff) else np.nan
        fa_rate = fas / len(same) if len(same) else np.nan
        rts = v.loc[v["rt_valid"], "reaction_time_ms"]
        sec = v[v["interference_correct_answer"].isin(["true", "false"])] if "interference_correct_answer" in v else v.iloc[0:0]
        sec_rts = sec.loc[sec.get("sec_correct", pd.Series(False, index=sec.index)) & sec["interference_reaction_time_ms"].notna(),
                          "interference_reaction_time_ms"] if len(sec) else pd.Series(dtype=float)
        rows.append({
            "participant_id": pid, "condition": cond,
            "n_trials": len(g), "n_valid": n, "n_invalid": int((~g["valid"]).sum()),
            "n_timeouts": int(v["timeout"].sum()), "n_answered": n_ans, "n_correct": int(v["correct"].sum()),
            "n_anticipatory": int(v["anticipatory"].sum()),
            "accuracy": v["correct"].mean() if n else np.nan,
            "accuracy_answered": v.loc[v["answered"], "correct"].mean() if n_ans else np.nan,
            "error_rate": 1 - v["correct"].mean() if n else np.nan,
            "timeout_rate": v["timeout"].mean() if n else np.nan,
            "mean_rt": rts.mean() if len(rts) else np.nan,
            "median_rt": rts.median() if len(rts) else np.nan,
            "n_rt": int(len(rts)),
            "hit_rate": hit_rate, "fa_rate": fa_rate,
            "dprime": dprime_loglinear(hits, len(diff), fas, len(same)),
            "k_pashler": pashler_k(hit_rate, fa_rate, n_items),
            "sec_accuracy": sec["sec_correct"].mean() if len(sec) and "sec_correct" in sec else np.nan,
            "sec_mean_rt": sec_rts.mean() if len(sec_rts) else np.nan,
            "same_key_prop": (v.loc[v["answered"], "participant_response"].value_counts(normalize=True).max()
                              if n_ans else np.nan),
        })
    return pd.DataFrame(rows)


def wide_summary(pcm: pd.DataFrame, ct: pd.DataFrame, ies_min_accuracy: float = 0.6) -> pd.DataFrame:
    """Participant_Summary layout: one row per participant (costs: positive = worse under interference)."""
    if pcm.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=sorted(pcm["participant_id"].unique()))
    out.index.name = "participant_id"
    for c, name in COND_NAMES.items():
        sub = pcm[pcm["condition"] == c].set_index("participant_id")
        out[f"{name}_accuracy"] = sub["accuracy"]
        out[f"{name}_accuracy_answered"] = sub["accuracy_answered"]
        out[f"{name}_mean_correct_rt_ms"] = sub["mean_rt"]
        out[f"{name}_median_correct_rt_ms"] = sub["median_rt"]
        out[f"{name}_timeout_rate"] = sub["timeout_rate"]
        out[f"{name}_dprime"] = sub["dprime"]
        out[f"{name}_k"] = sub["k_pashler"]
        out[f"{name}_n_valid"] = sub["n_valid"]
        if c in ("B", "C"):
            out[f"{name}_secondary_accuracy"] = sub["sec_accuracy"]
            out[f"{name}_secondary_mean_rt_ms"] = sub["sec_mean_rt"]
    out["numerical_accuracy_cost"] = out["control_accuracy"] - out["numerical_accuracy"]
    out["visual_accuracy_cost"] = out["control_accuracy"] - out["visual_accuracy"]
    out["numerical_rt_cost_ms"] = out["numerical_mean_correct_rt_ms"] - out["control_mean_correct_rt_ms"]
    out["visual_rt_cost_ms"] = out["visual_mean_correct_rt_ms"] - out["control_mean_correct_rt_ms"]
    out["mean_accuracy_cost"] = out[["numerical_accuracy_cost", "visual_accuracy_cost"]].mean(axis=1)
    out["mean_rt_cost_ms"] = out[["numerical_rt_cost_ms", "visual_rt_cost_ms"]].mean(axis=1)
    valid = ct[ct["valid"]]
    g = valid.groupby("participant_id")
    out["overall_accuracy"] = g["correct"].mean()
    out["timeout_rate"] = g["timeout"].mean()
    out["overall_mean_correct_rt_ms"] = valid[valid["rt_valid"]].groupby("participant_id")["reaction_time_ms"].mean()
    out["n_valid_trials"] = g.size()
    out["n_invalid_trials"] = ct[~ct["valid"]].groupby("participant_id").size().reindex(out.index).fillna(0).astype(int)
    out["same_key_proportion"] = valid[valid["answered"]].groupby("participant_id")["participant_response"].agg(
        lambda s: s.value_counts(normalize=True).max())
    acc_cols = ["control_accuracy", "numerical_accuracy", "visual_accuracy"]
    ok = (out[acc_cols] >= ies_min_accuracy).all(axis=1)
    for name in COND_NAMES.values():
        out[f"{name}_ies"] = np.where(ok, out[f"{name}_mean_correct_rt_ms"] / out[f"{name}_accuracy"], np.nan)
    return out.reset_index()
