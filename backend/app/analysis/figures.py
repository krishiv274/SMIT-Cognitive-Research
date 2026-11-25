"""Publication-quality figures (Matplotlib) generated from genuine data only.

Every figure: descriptive title, labelled axes with units, sample size, 95% CIs
where appropriate, individual observations where useful, colour-blind-safe
palette (Okabe–Ito). Figures are skipped (with a recorded reason) when the data
needed for them are unavailable or insufficient.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from . import stats as S  # noqa: E402
from .metrics import COND_LABELS  # noqa: E402

OKABE = {"A": "#0072B2", "B": "#E69F00", "C": "#009E73"}
GREY = "#666666"
SHORT = {"A": "Control", "B": "Numerical", "C": "Visual"}
ACC = {"A": "control_accuracy", "B": "numerical_accuracy", "C": "visual_accuracy"}
RT = {"A": "control_mean_correct_rt_ms", "B": "numerical_mean_correct_rt_ms", "C": "visual_mean_correct_rt_ms"}

plt.rcParams.update({
    "figure.dpi": 100, "savefig.dpi": 200, "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "axes.spines.top": False, "axes.spines.right": False, "figure.constrained_layout.use": True,
    "svg.fonttype": "none",
})


class FigureSet:
    def __init__(self, out_dir: Path):
        self.dir = out_dir / "figures"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.items: list[dict] = []

    def save(self, fig, fid: str, title: str, n: int | None, note: str = "") -> None:
        files = {}
        for ext in ("png", "svg", "pdf"):
            p = self.dir / f"{fid}.{ext}"
            fig.savefig(p, bbox_inches="tight")
            files[ext] = p.name
        plt.close(fig)
        self.items.append({"id": fid, "title": title, "files": files, "n": n, "note": note, "available": True})

    def skip(self, fid: str, title: str, reason: str) -> None:
        self.items.append({"id": fid, "title": title, "files": {}, "n": None, "note": reason, "available": False})


def _num(s) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def _mean_ci(x: pd.Series) -> tuple[float, float, float]:
    d = S.describe(x)
    return d.get("mean") or np.nan, d.get("ci_low") or np.nan, d.get("ci_high") or np.nan


def _cond_plot(ax, inc: pd.DataFrame, cols: dict, ylabel: str, pct: bool):
    rng = np.random.default_rng(0)
    complete = inc[[cols[c] for c in "ABC"]].apply(pd.to_numeric, errors="coerce").dropna()
    for i, c in enumerate("ABC"):
        vals = complete[cols[c]] * (100 if pct else 1)
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(vals)), vals, s=14, color=OKABE[c], alpha=0.45, edgecolor="none", zorder=2)
        m, lo, hi = _mean_ci(vals)
        ax.errorbar(i + 0.28, m, yerr=[[m - lo], [hi - m]], fmt="o", color="black", ms=7, capsize=5, lw=1.6, zorder=3)
    ax.set_xticks(range(3), [f"{SHORT[c]}\n({c})" for c in "ABC"])
    ax.set_xlim(-0.5, 2.7)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("Interference condition")
    return len(complete)


def make_all(out_dir: Path, inc: pd.DataFrame, ct: pd.DataFrame, results: dict, frames: dict) -> list[dict]:
    fs = FigureSet(out_dir)
    n = len(inc)
    trial_ids = set(inc.loc[~inc.get("summary_only", pd.Series(False, index=inc.index)).astype(bool), "participant_id"])
    ctv = ct[ct["participant_id"].isin(trial_ids) & ct["valid"]] if len(ct) else ct

    # 1 / 2 condition means
    for fid, cols, lab, pct, title in (("01_accuracy_by_condition", ACC, "Recognition accuracy (% correct)", True, "Mean recognition accuracy by interference condition"),
                                       ("02_rt_by_condition", RT, "Mean correct RT (ms)", False, "Mean correct recognition reaction time by condition")):
        if n < 2:
            fs.skip(fid, title, "fewer than 2 eligible participants")
            continue
        fig, ax = plt.subplots(figsize=(5.2, 4.2))
        k = _cond_plot(ax, inc, cols, lab, pct)
        if pct:
            ax.axhline(50, ls=":", color=GREY, lw=1)
            ax.text(2.62, 51, "chance", color=GREY, fontsize=8, ha="right")
        ax.set_title(f"{title}\n(dots = participants; black = mean ± 95% CI; N = {k})")
        fs.save(fig, fid, title, k)

    # 3 accuracy distributions
    if n >= 2:
        fig, ax = plt.subplots(figsize=(5.2, 4.2))
        data = [(_num(inc[ACC[c]]) * 100).dropna() for c in "ABC"]
        bp = ax.boxplot(data, tick_labels=[SHORT[c] for c in "ABC"], patch_artist=True, widths=0.5, showfliers=False)
        for patch, c in zip(bp["boxes"], "ABC"):
            patch.set_facecolor(OKABE[c]); patch.set_alpha(0.35)
        for i, d in enumerate(data):
            ax.scatter(np.full(len(d), i + 1) + np.random.default_rng(1).uniform(-0.1, 0.1, len(d)), d, s=12, color="black", alpha=0.6)
        ax.set_ylabel("Recognition accuracy (% correct)"); ax.set_xlabel("Interference condition")
        ax.set_title(f"Distribution of participant accuracy by condition (N = {n})")
        fs.save(fig, "03_accuracy_distributions", "Accuracy distributions by condition", n)
    else:
        fs.skip("03_accuracy_distributions", "Accuracy distributions by condition", "fewer than 2 eligible participants")

    # 4 RT distributions (trial level)
    if len(ctv) and ctv["rt_valid"].sum() >= 10:
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.4), sharey=True)
        bins = np.linspace(0, ctv.loc[ctv["rt_valid"], "reaction_time_ms"].max() + 50, 30)
        for ax, c in zip(axes, "ABC"):
            r = ctv.loc[ctv["rt_valid"] & (ctv["condition"] == c), "reaction_time_ms"]
            ax.hist(r, bins=bins, color=OKABE[c], alpha=0.8)
            ax.axvline(r.median(), color="black", ls="--", lw=1)
            ax.set_title(f"{SHORT[c]} ({c}): {len(r)} correct trials")
            ax.set_xlabel("Correct RT (ms)")
        axes[0].set_ylabel("Number of trials")
        fig.suptitle(f"Trial-level correct RT distributions (dashed = median; {len(trial_ids)} participants)")
        fs.save(fig, "04_rt_distributions", "Reaction-time distributions by condition", len(trial_ids))
    else:
        fs.skip("04_rt_distributions", "Reaction-time distributions by condition", "trial-level RT data unavailable or fewer than 10 correct trials")

    # 5 individual performance (dot plot)
    if n >= 1:
        d = inc[["participant_id"] + list(ACC.values())].copy()
        d["mean"] = d[list(ACC.values())].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        d = d.sort_values("mean")
        fig, ax = plt.subplots(figsize=(6, max(3, 0.22 * len(d) + 1.2)))
        y = np.arange(len(d))
        for c, m in zip("ABC", ("o", "s", "^")):
            ax.scatter(_num(d[ACC[c]]) * 100, y, marker=m, color=OKABE[c], label=SHORT[c], s=28, zorder=3)
        ax.hlines(y, (d[list(ACC.values())].apply(pd.to_numeric, errors="coerce").min(axis=1) * 100),
                  (d[list(ACC.values())].apply(pd.to_numeric, errors="coerce").max(axis=1) * 100), color="#cccccc", lw=1, zorder=1)
        ax.set_yticks(y, d["participant_id"], fontsize=7)
        ax.set_xlabel("Recognition accuracy (% correct)")
        ax.legend(title="Condition", loc="lower right", fontsize=8)
        ax.set_title(f"Individual participant accuracy across conditions (N = {n})")
        fs.save(fig, "05_individual_performance", "Individual participant performance across conditions", n)

    # 6 paired lines (accuracy and RT)
    if n >= 2:
        fig, axes = plt.subplots(1, 2, figsize=(9, 4))
        for ax, cols, lab, scale in ((axes[0], ACC, "Accuracy (% correct)", 100), (axes[1], RT, "Mean correct RT (ms)", 1)):
            w = inc[[cols[c] for c in "ABC"]].apply(pd.to_numeric, errors="coerce").dropna() * scale
            for _, r in w.iterrows():
                ax.plot(range(3), r.values, color=GREY, alpha=0.35, lw=1, marker="o", ms=3)
            ax.plot(range(3), w.mean().values, color="black", lw=2.5, marker="o", ms=7, label="Mean")
            ax.set_xticks(range(3), [SHORT[c] for c in "ABC"])
            ax.set_ylabel(lab)
            ax.set_title(f"{lab.split(' (')[0]} (N = {len(w)})")
        fig.suptitle("Paired participant-level profiles across conditions (grey = individual participants)")
        fs.save(fig, "06_paired_profiles", "Paired participant-level line plots", n)
    else:
        fs.skip("06_paired_profiles", "Paired participant-level line plots", "fewer than 2 eligible participants")

    # 7 / 8 costs
    for fid, cols, lab, title, scale in (
            ("07_accuracy_costs", ("numerical_accuracy_cost", "visual_accuracy_cost"), "Accuracy cost (percentage points)\npositive = worse than control",
             "Accuracy interference costs", 100),
            ("08_rt_costs", ("numerical_rt_cost_ms", "visual_rt_cost_ms"), "RT cost (ms)\npositive = slower than control",
             "Reaction-time interference costs", 1)):
        w = inc[list(cols)].apply(pd.to_numeric, errors="coerce").dropna() * scale
        if len(w) < 2:
            fs.skip(fid, title, "fewer than 2 participants with both costs")
            continue
        fig, ax = plt.subplots(figsize=(4.8, 4.2))
        for i, (c, cond) in enumerate(zip(cols, "BC")):
            v = w[c]
            ax.scatter(i + np.random.default_rng(2).uniform(-0.1, 0.1, len(v)), v, color=OKABE[cond], alpha=0.5, s=14)
            m, lo, hi = _mean_ci(v)
            ax.errorbar(i + 0.25, m, yerr=[[m - lo], [hi - m]], fmt="o", color="black", capsize=5, ms=7)
        for _, r in w.iterrows():
            ax.plot([0, 1], r.values, color="#bbbbbb", lw=0.7, zorder=0)
        ax.axhline(0, color="black", lw=0.8)
        ax.set_xticks([0, 1], ["Numerical\n(A − B)" if scale == 100 else "Numerical\n(B − A)", "Visual\n(A − C)" if scale == 100 else "Visual\n(C − A)"])
        ax.set_xlim(-0.5, 1.6)
        ax.set_ylabel(lab)
        ax.set_title(f"{title} (mean ± 95% CI; N = {len(w)})")
        fs.save(fig, fid, title, len(w))

    # 9–11 scatter plots
    for fid, x, y, xl, yl, title, ys in (
            ("09_age_vs_accuracy", "age", "overall_accuracy", "Age (years)", "Overall accuracy (% correct)", "Age versus overall accuracy", 100),
            ("10_age_vs_rt", "age", "overall_mean_correct_rt_ms", "Age (years)", "Overall mean correct RT (ms)", "Age versus overall reaction time", 1),
            ("11_accuracy_vs_rt", "overall_mean_correct_rt_ms", "overall_accuracy", "Overall mean correct RT (ms)", "Overall accuracy (% correct)", "Accuracy versus reaction time (speed–accuracy)", 100)):
        d = inc[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(d) < 4 or d[x].nunique() < 2:
            fs.skip(fid, title, "fewer than 4 participants with both variables, or no variance")
            continue
        corr = S.correlation(d[x], d[y])
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.scatter(d[x], d[y] * ys, color="#0072B2", alpha=0.75, s=26)
        ax.set_xlabel(xl); ax.set_ylabel(yl)
        lab = "r" if corr.get("method") == "pearson" else "ρ"
        txt = (f"{corr.get('method', '').title()} {lab} = {corr['r']:.2f}, 95% CI [{corr['ci_low']:.2f}, {corr['ci_high']:.2f}], "
               f"p = {S._f(corr['p']):.3f}, n = {corr['n']}" if corr.get("r") is not None else corr.get("note", ""))
        ax.set_title(f"{title}\n{txt}", fontsize=9)
        ax.text(0.01, -0.2, "Exploratory; association does not imply causation.", transform=ax.transAxes, fontsize=7, color=GREY)
        fs.save(fig, fid, title, len(d))

    # 12 correlation heatmap
    cm = results.get("exploratory", {}).get("correlation_matrix")
    if cm and len(cm["variables"]) >= 3:
        r = np.array(cm["r"], dtype=float)
        labels = [v.replace("_mean_correct_rt_ms", " RT").replace("_accuracy", " acc").replace("_cost", " cost").replace("_ms", "").replace("_", " ")
                  for v in cm["variables"]]
        fig, ax = plt.subplots(figsize=(7.5, 6.5))
        im = ax.imshow(r, cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(len(labels)), labels, rotation=60, ha="right", fontsize=7)
        ax.set_yticks(range(len(labels)), labels, fontsize=7)
        for i in range(len(labels)):
            for j in range(len(labels)):
                if not np.isnan(r[i, j]):
                    ax.text(j, i, f"{r[i, j]:.2f}", ha="center", va="center", fontsize=6, color="white" if abs(r[i, j]) > 0.6 else "black")
        fig.colorbar(im, ax=ax, label="Spearman ρ")
        ax.set_title(f"Correlation matrix of participant-level variables (Spearman; N = {n})\nExploratory; no causal interpretation")
        fs.save(fig, "12_correlation_heatmap", "Correlation heatmap", n)
    else:
        fs.skip("12_correlation_heatmap", "Correlation heatmap", "fewer than 3 variables with sufficient data")

    # 13 / 14 group comparisons
    for fid, var, title in (("13_gender_comparison", "gender", "Exploratory gender comparison"),
                            ("14_course_comparison", "academic_course", "Exploratory academic-course comparison")):
        g = inc[[var, "overall_accuracy"]].copy()
        g[var] = g[var].fillna("Missing")
        groups = [(k, _num(v["overall_accuracy"]).dropna() * 100) for k, v in g.groupby(var)]
        groups = [x for x in groups if len(x[1])]
        if len(groups) < 2:
            fs.skip(fid, title, "fewer than two groups with data")
            continue
        fig, ax = plt.subplots(figsize=(max(5, 1.2 * len(groups) + 2), 4.2))
        for i, (k, v) in enumerate(groups):
            ax.scatter(i + np.random.default_rng(3).uniform(-0.1, 0.1, len(v)), v, s=16, alpha=0.6, color="#0072B2")
            if len(v) >= 2:
                m, lo, hi = _mean_ci(v)
                ax.errorbar(i + 0.25, m, yerr=[[m - lo], [hi - m]], fmt="o", color="black", capsize=4)
        ax.set_xticks(range(len(groups)), [f"{k}\n(n = {len(v)})" for k, v in groups], fontsize=8)
        ax.set_ylabel("Overall accuracy (% correct)")
        ax.set_title(f"{title} (exploratory; small groups are not tested inferentially)")
        fs.save(fig, fid, title, n)

    # 15 demographics
    if n >= 1:
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
        ages = _num(inc["age"]).dropna()
        if len(ages):
            axes[0].hist(ages, bins=range(int(ages.min()), int(ages.max()) + 2), color="#56B4E9", edgecolor="white")
        axes[0].set_xlabel("Age (years)"); axes[0].set_ylabel("Participants"); axes[0].set_title(f"Age (n = {len(ages)})")
        for ax, var, lab in ((axes[1], "gender", "Gender"), (axes[2], "academic_course", "Academic course")):
            vc = inc[var].fillna("Missing").value_counts()
            ax.barh(vc.index.astype(str), vc.values, color="#CC79A7")
            ax.set_xlabel("Participants"); ax.set_title(lab)
            ax.tick_params(axis="y", labelsize=8)
        fig.suptitle(f"Participant demographics (eligible participants, N = {n})")
        fs.save(fig, "15_demographics", "Participant demographic distributions", n)

    # 16 learning / fatigue
    bp = results.get("exploratory", {}).get("block_position")
    tt = results.get("exploratory", {}).get("trial_trend")
    if bp and tt:
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
        tdf = pd.DataFrame(tt)
        axes[0].plot(tdf["trial_in_block"], tdf["accuracy"] * 100, marker="o", color="#0072B2")
        axes[0].set_xlabel("Trial position within block"); axes[0].set_ylabel("Accuracy (% correct)")
        axes[0].set_title("Accuracy by trial position (all blocks pooled)")
        desc = bp["accuracy"]["descriptives"]
        ks = sorted(desc, key=int)
        means = [desc[k]["mean"] * 100 for k in ks]
        err = [[(desc[k]["mean"] - (desc[k]["ci_low"] or desc[k]["mean"])) * 100 for k in ks],
               [((desc[k]["ci_high"] or desc[k]["mean"]) - desc[k]["mean"]) * 100 for k in ks]]
        axes[1].errorbar([int(k) for k in ks], means, yerr=err, marker="o", capsize=5, color="#D55E00")
        axes[1].set_xticks([int(k) for k in ks], [f"Block {k}" for k in ks])
        axes[1].set_ylabel("Accuracy (% correct)"); axes[1].set_title(f"Accuracy by block position (mean ± 95% CI; N = {desc[ks[0]]['n']})")
        fig.suptitle("Learning / fatigue trends across the session (exploratory)")
        fs.save(fig, "16_learning_fatigue", "Trial-level learning or fatigue trends", len(trial_ids))
    else:
        fs.skip("16_learning_fatigue", "Trial-level learning or fatigue trends", "trial-level data unavailable")

    # 17 secondary task
    sb, sc = "numerical_secondary_accuracy", "visual_secondary_accuracy"
    w = inc[[sb, sc]].apply(pd.to_numeric, errors="coerce").dropna() * 100 if sb in inc and sc in inc else pd.DataFrame()
    if len(w) >= 2:
        fig, ax = plt.subplots(figsize=(4.8, 4.2))
        for _, r in w.iterrows():
            ax.plot([0, 1], r.values, color="#bbbbbb", lw=0.8)
        for i, (c, cond) in enumerate(((sb, "B"), (sc, "C"))):
            ax.scatter(np.full(len(w), i), w[c], color=OKABE[cond], s=16, alpha=0.7)
            m, lo, hi = _mean_ci(w[c])
            ax.errorbar(i + 0.15, m, yerr=[[m - lo], [hi - m]], fmt="o", color="black", capsize=5)
        ax.set_xticks([0, 1], ["Arithmetic (B)", "Symmetry (C)"])
        ax.set_xlim(-0.4, 1.4)
        ax.set_ylabel("Secondary-task accuracy (% correct)")
        ax.set_title(f"Interference-task engagement (manipulation check; N = {len(w)})")
        fs.save(fig, "17_secondary_task_accuracy", "Secondary interference-task accuracy", len(w))
    else:
        fs.skip("17_secondary_task_accuracy", "Secondary interference-task accuracy", "secondary-task data unavailable")

    # 18 timing quality and missing data
    dq = results.get("data_quality", {})
    if dq.get("trial_categories"):
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
        allct = ct if len(ct) else pd.DataFrame()
        d = (_num(allct["measured_stimulus_duration_ms"]) - _num(allct["planned_stimulus_duration_ms"])).dropna() if len(allct) else pd.Series(dtype=float)
        if len(d):
            axes[0].hist(d, bins=30, color="#009E73")
            axes[0].set_xlabel("Measured − planned memory-stimulus duration (ms)")
            axes[0].set_ylabel("Trials")
            axes[0].set_title(f"Memory-stimulus timing deviation ({len(d)} trials)")
        else:
            axes[0].text(0.5, 0.5, "No measured durations\n(e.g. imported without timing columns)", ha="center", va="center")
            axes[0].set_axis_off()
        cats = dq["trial_categories"]
        order = ["correct", "incorrect", "timeout", "technically_invalid"]
        vals = [cats.get(k, 0) for k in order]
        axes[1].bar(["Correct", "Incorrect", "Missing\n(timeout)", "Technically\ninvalid"], vals,
                    color=["#009E73", "#D55E00", "#E69F00", "#999999"])
        for i, v in enumerate(vals):
            axes[1].text(i, v, str(v), ha="center", va="bottom", fontsize=8)
        axes[1].set_ylabel("Experimental trials")
        axes[1].set_title("Trial outcome categories (all main-study trials)")
        fig.suptitle("Timing quality and missing-data summary")
        fs.save(fig, "18_timing_quality_missing_data", "Timing quality and missing-data summaries", None)
    else:
        fs.skip("18_timing_quality_missing_data", "Timing quality and missing-data summaries", "no trial-level data")
    return fs.items
