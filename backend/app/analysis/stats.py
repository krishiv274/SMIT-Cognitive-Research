"""Statistical procedures used by the SMIT analysis pipeline.

Implemented directly with NumPy/SciPy so every formula is visible and testable;
results are cross-validated against Pingouin in the unit tests.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests


def _f(x: Any) -> float | None:
    """JSON-safe float."""
    if x is None:
        return None
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if (math.isnan(x) or math.isinf(x)) else x


# ---------------------------------------------------------------------------
# Descriptives
# ---------------------------------------------------------------------------

def describe(values, ci: float = 0.95) -> dict:
    x = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    n = len(x)
    if n == 0:
        return {"n": 0}
    mean = x.mean()
    sd = x.std(ddof=1) if n > 1 else float("nan")
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    if n > 1:
        h = stats.t.ppf(0.5 + ci / 2, n - 1) * sd / math.sqrt(n)
        lo, hi = mean - h, mean + h
    else:
        lo = hi = float("nan")
    return {"n": n, "mean": _f(mean), "sd": _f(sd), "se": _f(sd / math.sqrt(n)) if n > 1 else None,
            "median": _f(med), "min": _f(x.min()), "max": _f(x.max()), "q1": _f(q1), "q3": _f(q3),
            "iqr": _f(q3 - q1), "ci_low": _f(lo), "ci_high": _f(hi)}


# ---------------------------------------------------------------------------
# Normality
# ---------------------------------------------------------------------------

def shapiro(values) -> dict:
    x = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    if len(x) < 3:
        return {"n": len(x), "W": None, "p": None, "note": "fewer than 3 observations"}
    if np.ptp(x) == 0:
        return {"n": len(x), "W": None, "p": None, "note": "all values identical (no variance)"}
    w, p = stats.shapiro(x)
    return {"n": len(x), "W": _f(w), "p": _f(p)}


# ---------------------------------------------------------------------------
# Paired comparisons
# ---------------------------------------------------------------------------

def paired_t(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    d = x - y
    n = len(d)
    out: dict = {"test": "paired t-test", "n": n, "mean_x": _f(x.mean()) if n else None,
                 "mean_y": _f(y.mean()) if n else None, "mean_diff": _f(d.mean()) if n else None}
    if n < 2:
        return {**out, "note": "fewer than 2 pairs"}
    sd = d.std(ddof=1)
    if sd == 0:
        return {**out, "sd_diff": 0.0, "note": "all paired differences identical; t-test undefined"}
    se = sd / math.sqrt(n)
    t = d.mean() / se
    p = 2 * stats.t.sf(abs(t), n - 1)
    h = stats.t.ppf(0.975, n - 1) * se
    dz = d.mean() / sd
    gz = dz * (1 - 3 / (4 * (n - 1) - 1)) if n > 2 else None
    return {**out, "sd_diff": _f(sd), "t": _f(t), "df": n - 1, "p": _f(p), "ci_low": _f(d.mean() - h),
            "ci_high": _f(d.mean() + h), "cohens_dz": _f(dz), "hedges_gz": _f(gz)}


def wilcoxon(x, y) -> dict:
    x, y = np.asarray(x, float), np.asarray(y, float)
    d = x - y
    nz = d[d != 0]
    out = {"test": "Wilcoxon signed-rank", "n": len(d), "n_nonzero": int(len(nz)),
           "median_diff": _f(np.median(d)) if len(d) else None}
    if len(nz) < 1:
        return {**out, "note": "all paired differences are zero"}
    ranks = stats.rankdata(np.abs(nz))
    r_plus, r_minus = ranks[nz > 0].sum(), ranks[nz < 0].sum()
    rbc = (r_plus - r_minus) / ranks.sum()
    try:
        res = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
        stat, p = res.statistic, res.pvalue
    except ValueError as exc:
        return {**out, "note": str(exc), "rank_biserial": _f(rbc)}
    return {**out, "W": _f(stat), "p": _f(p), "rank_biserial": _f(rbc)}


def holm(pvalues: list[float | None]) -> list[float | None]:
    idx = [i for i, p in enumerate(pvalues) if p is not None]
    out: list[float | None] = [None] * len(pvalues)
    if not idx:
        return out
    adj = multipletests([pvalues[i] for i in idx], method="holm")[1]
    for i, a in zip(idx, adj):
        out[i] = _f(a)
    return out


# ---------------------------------------------------------------------------
# Repeated-measures ANOVA (one within factor) with Mauchly + Greenhouse–Geisser
# ---------------------------------------------------------------------------

def _orthonormal_contrasts(k: int) -> np.ndarray:
    # Helmert-like orthonormal contrasts (k x (k-1))
    c = np.zeros((k, k - 1))
    for j in range(1, k):
        c[:j, j - 1] = 1
        c[j, j - 1] = -j
        c[:, j - 1] /= np.linalg.norm(c[:, j - 1])
    return c


def mauchly(Y: np.ndarray) -> dict:
    n, k = Y.shape
    p = k - 1
    C = _orthonormal_contrasts(k)
    Z = Y @ C
    S = np.cov(Z, rowvar=False, ddof=1)
    S = np.atleast_2d(S)
    tr = np.trace(S)
    if tr <= 0:
        return {"W": None, "chi2": None, "df": None, "p": None, "gg_epsilon": None, "note": "no variance"}
    W = np.linalg.det(S) / (tr / p) ** p
    gg = tr**2 / (p * np.trace(S @ S))
    hf = min(1.0, (n * (k - 1) * gg - 2) / ((k - 1) * (n - 1 - (k - 1) * gg))) if n - 1 - (k - 1) * gg != 0 else None
    if p == 1:
        return {"W": 1.0, "chi2": 0.0, "df": 0, "p": 1.0, "gg_epsilon": 1.0, "hf_epsilon": 1.0,
                "note": "sphericity holds trivially with two levels"}
    f = (2 * p**2 + p + 2) / (6 * p)
    df = p * (p + 1) / 2 - 1
    if W <= 0:
        return {"W": _f(W), "chi2": None, "df": df, "p": None, "gg_epsilon": _f(gg), "hf_epsilon": _f(hf),
                "note": "singular covariance (too few participants)"}
    chi2 = -(n - 1 - f) * math.log(W)
    pv = stats.chi2.sf(chi2, df)
    return {"W": _f(W), "chi2": _f(chi2), "df": df, "p": _f(pv), "gg_epsilon": _f(gg), "hf_epsilon": _f(hf)}


def rm_anova(wide: pd.DataFrame) -> dict:
    """wide: rows = participants, columns = conditions (complete cases only)."""
    Y = wide.dropna().to_numpy(dtype=float)
    n, k = Y.shape
    if n < 3:
        return {"test": "repeated-measures ANOVA", "n": n, "note": "fewer than 3 complete participants"}
    grand = Y.mean()
    ss_subj = k * ((Y.mean(axis=1) - grand) ** 2).sum()
    ss_cond = n * ((Y.mean(axis=0) - grand) ** 2).sum()
    ss_total = ((Y - grand) ** 2).sum()
    ss_err = ss_total - ss_subj - ss_cond
    df1, df2 = k - 1, (k - 1) * (n - 1)
    if ss_err <= 1e-15:
        return {"test": "repeated-measures ANOVA", "n": n, "note": "no residual variance; F undefined"}
    F = (ss_cond / df1) / (ss_err / df2)
    p = stats.f.sf(F, df1, df2)
    sph = mauchly(Y)
    eps = sph.get("gg_epsilon") or 1.0
    p_gg = stats.f.sf(F, df1 * eps, df2 * eps)
    return {"test": "repeated-measures ANOVA", "n": n, "k": k, "F": _f(F), "df1": df1, "df2": df2, "p": _f(p),
            "partial_eta_sq": _f(ss_cond / (ss_cond + ss_err)), "ss_condition": _f(ss_cond), "ss_error": _f(ss_err),
            "ss_subjects": _f(ss_subj), "sphericity": sph, "gg_df1": _f(df1 * eps), "gg_df2": _f(df2 * eps),
            "p_gg": _f(p_gg), "sphericity_violated": bool(sph.get("p") is not None and sph["p"] < 0.05)}


def friedman(wide: pd.DataFrame) -> dict:
    Y = wide.dropna().to_numpy(dtype=float)
    n, k = Y.shape
    if n < 3:
        return {"test": "Friedman", "n": n, "note": "fewer than 3 complete participants"}
    if np.all(Y == Y[:, [0]]):
        return {"test": "Friedman", "n": n, "note": "all conditions identical within every participant"}
    chi2, p = stats.friedmanchisquare(*[Y[:, j] for j in range(k)])
    return {"test": "Friedman", "n": n, "chi2": _f(chi2), "df": k - 1, "p": _f(p), "kendalls_w": _f(chi2 / (n * (k - 1)))}


# ---------------------------------------------------------------------------
# Correlations
# ---------------------------------------------------------------------------

def correlation(x, y, alpha_normal: float = 0.05, method: str | None = None) -> dict:
    df = pd.DataFrame({"x": pd.to_numeric(pd.Series(x), errors="coerce"),
                       "y": pd.to_numeric(pd.Series(y), errors="coerce")}).dropna()
    n = len(df)
    out: dict = {"n": n}
    if n < 4:
        return {**out, "note": "fewer than 4 complete pairs; correlation not computed"}
    if df["x"].nunique() < 2 or df["y"].nunique() < 2:
        return {**out, "note": "a variable has no variance"}
    if method is None:
        sx, sy = shapiro(df["x"]), shapiro(df["y"])
        normal = all(s.get("p") is not None and s["p"] > alpha_normal for s in (sx, sy))
        enough = df["x"].nunique() >= 5 and df["y"].nunique() >= 5
        method = "pearson" if (normal and enough) else "spearman"
        out["method_reason"] = ("both variables consistent with normality (Shapiro–Wilk p > .05) and ≥ 5 distinct values"
                                if method == "pearson" else
                                "normality rejected or too few distinct values → rank-based Spearman correlation")
    if method == "pearson":
        r, p = stats.pearsonr(df["x"], df["y"])
        se = 1 / math.sqrt(n - 3)
    else:
        r, p = stats.spearmanr(df["x"], df["y"])
        se = math.sqrt((1 + r**2 / 2) / (n - 3))  # Bonett & Wright (2000)
    r = float(r)
    if abs(r) < 1:
        z = math.atanh(r)
        lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    else:
        lo = hi = r
    return {**out, "method": method, "r": _f(r), "p": _f(p), "ci_low": _f(lo), "ci_high": _f(hi)}


# ---------------------------------------------------------------------------
# Independent groups
# ---------------------------------------------------------------------------

def hedges_g(a: np.ndarray, b: np.ndarray) -> float | None:
    n1, n2 = len(a), len(b)
    if n1 < 2 or n2 < 2:
        return None
    sp = math.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    if sp == 0:
        return None
    d = (a.mean() - b.mean()) / sp
    return d * (1 - 3 / (4 * (n1 + n2) - 9))


def two_groups(a, b, labels: tuple[str, str]) -> dict:
    a = pd.to_numeric(pd.Series(a), errors="coerce").dropna().to_numpy(float)
    b = pd.to_numeric(pd.Series(b), errors="coerce").dropna().to_numpy(float)
    out = {"groups": list(labels), "n": [len(a), len(b)], "means": [_f(a.mean()), _f(b.mean())]}
    if len(a) < 2 or len(b) < 2:
        return {**out, "note": "a group has fewer than 2 observations"}
    t, p = stats.ttest_ind(a, b, equal_var=False)
    v1, v2 = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    df = (v1 + v2) ** 2 / (v1**2 / (len(a) - 1) + v2**2 / (len(b) - 1)) if (v1 + v2) > 0 else None
    u, pu = stats.mannwhitneyu(a, b, alternative="two-sided")
    rbc = 1 - 2 * u / (len(a) * len(b))
    return {**out, "welch_t": {"t": _f(t), "df": _f(df), "p": _f(p), "hedges_g": _f(hedges_g(a, b))},
            "mann_whitney": {"U": _f(u), "p": _f(pu), "rank_biserial": _f(-rbc)}}


def welch_anova(groups: dict[str, np.ndarray]) -> dict:
    names = list(groups)
    k = len(names)
    ns = np.array([len(groups[g]) for g in names], float)
    ms = np.array([groups[g].mean() for g in names])
    vs = np.array([groups[g].var(ddof=1) for g in names])
    if np.any(vs == 0) or np.any(ns < 2):
        return {"note": "a group has fewer than 2 observations or zero variance"}
    w = ns / vs
    W = w.sum()
    mw = (w * ms).sum() / W
    A = (w * (ms - mw) ** 2).sum() / (k - 1)
    lam = ((1 - w / W) ** 2 / (ns - 1)).sum()
    B = 1 + 2 * (k - 2) / (k**2 - 1) * lam
    F = A / B
    df2 = (k**2 - 1) / (3 * lam)
    p = stats.f.sf(F, k - 1, df2)
    allv = np.concatenate([groups[g] for g in names])
    ss_b = (ns * (ms - allv.mean()) ** 2).sum()
    ss_t = ((allv - allv.mean()) ** 2).sum()
    return {"F": _f(F), "df1": k - 1, "df2": _f(df2), "p": _f(p), "eta_sq": _f(ss_b / ss_t) if ss_t > 0 else None}


def multi_groups(groups: dict[str, Any]) -> dict:
    g = {k: pd.to_numeric(pd.Series(v), errors="coerce").dropna().to_numpy(float) for k, v in groups.items()}
    out = {"groups": list(g), "n": [len(v) for v in g.values()], "means": [_f(v.mean()) for v in g.values()]}
    wa = welch_anova(g)
    allv = [v for v in g.values()]
    N = sum(len(v) for v in allv)
    try:
        H, p = stats.kruskal(*allv)
        eps2 = H * (N + 1) / (N**2 - 1)
        kw = {"H": _f(H), "df": len(allv) - 1, "p": _f(p), "epsilon_sq": _f(eps2)}
    except ValueError as exc:
        kw = {"note": str(exc)}
    return {**out, "welch_anova": wa, "kruskal_wallis": kw}
