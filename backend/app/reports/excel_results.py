"""SMIT_Statistical_Results.xlsx from an analysis results dictionary."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill

HEAD = PatternFill("solid", fgColor="1F3A93")


def _desc_rows(d: dict) -> list[dict]:
    rows = []
    for measure, conds in d.items():
        if measure == "trial_level":
            continue
        for c, s in conds.items():
            if isinstance(s, dict) and "n" in s:
                rows.append({"measure": measure, "condition": c, **s})
    return rows


def write_results_workbook(results: dict, path: Path) -> Path:
    m = results["meta"]
    sheets: dict[str, pd.DataFrame] = {}
    sheets["Summary"] = pd.DataFrame([
        ("Status", m["status"]), ("Generated", m["generated_at"]), ("Dataset hash", m["dataset_hash"]),
        ("Registered main participants", m["n_registered"]), ("Included", m["n_included"]), ("Excluded", m["n_excluded"]),
        ("Summary-only participants", m["n_summary_only"]), ("Experiment versions", ", ".join(m["experiment_versions"])),
        ("Messages", " | ".join(m["messages"])), ("Note", "De-identified. Hypothesis decisions are rule-based and must be reviewed."),
    ] + [(f"software: {k}", v) for k, v in m["software"].items()] + [(f"analysis: {k}", v) for k, v in m["analysis_config"].items()],
        columns=["item", "value"])
    if results.get("hypotheses"):
        sheets["Hypotheses"] = pd.DataFrame(results["hypotheses"])
    if results.get("descriptives"):
        sheets["Descriptives"] = pd.DataFrame(_desc_rows(results["descriptives"]))
        if "trial_level" in results["descriptives"]:
            sheets["Trial_Level"] = pd.DataFrame([{"condition": k, **v} for k, v in results["descriptives"]["trial_level"].items()])
    for key, conf in (results.get("confirmatory") or {}).items():
        if conf.get("status") != "ok":
            sheets[f"Confirm_{key}"] = pd.DataFrame([{"note": conf.get("note")}])
            continue
        a, f = conf["rm_anova"], conf["friedman"]
        sph = a.get("sphericity", {})
        om = [{"test": "RM-ANOVA", "F": a.get("F"), "df1": a.get("df1"), "df2": a.get("df2"), "p": a.get("p"), "partial_eta_sq": a.get("partial_eta_sq"),
               "gg_epsilon": sph.get("gg_epsilon"), "p_gg": a.get("p_gg"), "mauchly_W": sph.get("W"), "mauchly_p": sph.get("p")},
              {"test": "Friedman", "chi2": f.get("chi2"), "df1": f.get("df"), "p": f.get("p"), "kendalls_w": f.get("kendalls_w")}]
        pw = []
        for p in conf["pairwise"]:
            t, w = p["t_test"], p["wilcoxon"]
            pw.append({"comparison": p["pair"], "hypothesis": p["hypothesis"], "primary": p["primary"], "mean_diff": t.get("mean_diff"),
                       "ci_low": t.get("ci_low"), "ci_high": t.get("ci_high"), "t": t.get("t"), "df": t.get("df"), "p": t.get("p"),
                       "p_holm": t.get("p_holm"), "cohens_dz": t.get("cohens_dz"), "hedges_gz": t.get("hedges_gz"), "wilcoxon_W": w.get("W"),
                       "wilcoxon_p": w.get("p"), "wilcoxon_p_holm": w.get("p_holm"), "rank_biserial": w.get("rank_biserial")})
        norm = [{"difference": k, **v} for k, v in conf["normality"].items()]
        sheets[f"Confirm_{key}"] = pd.concat([pd.DataFrame([{"route": conf["route"], "reason": conf["route_reason"]}]),
                                              pd.DataFrame(om), pd.DataFrame(pw), pd.DataFrame(norm)], ignore_index=True)
    ex = results.get("exploratory") or {}
    if ex.get("correlations"):
        sheets["Correlations"] = pd.DataFrame(ex["correlations"])
    if ex.get("correlation_matrix"):
        cm = ex["correlation_matrix"]
        sheets["Correlation_Matrix"] = pd.DataFrame(cm["r"], index=cm["variables"], columns=cm["variables"]).reset_index()
    demo_rows = []
    for var, dm in (ex.get("demographics") or {}).items():
        for dv, groups in dm.get("groups", {}).items():
            for g, s in groups.items():
                demo_rows.append({"variable": var, "dv": dv, "group": g, **s})
        for dv, t in dm.get("tests", {}).items():
            demo_rows.append({"variable": var, "dv": dv, "group": "TEST", "result": str(t)})
        if dm.get("note"):
            demo_rows.append({"variable": var, "group": "NOTE", "result": dm["note"]})
    if demo_rows:
        sheets["Demographics"] = pd.DataFrame(demo_rows)
    if results.get("exclusions"):
        sheets["Exclusions"] = pd.DataFrame([{**e, "rules": ", ".join(e["rules"]), "reasons": "; ".join(e["reasons"])} for e in results["exclusions"]])
    sheets["Data_Quality"] = pd.DataFrame([{"item": k, "value": str(v)} for k, v in results.get("data_quality", {}).items()])
    if results.get("participant_summary"):
        ps = pd.DataFrame(results["participant_summary"])
        ps = ps.drop(columns=[c for c in ps.columns if c in ("exclusion_rules",)], errors="ignore")
        sheets["Participant_Summary"] = ps
    sheets["Figures"] = pd.DataFrame([{"id": f["id"], "title": f["title"], "available": f["available"], "n": f.get("n"), "note": f.get("note"),
                                       "files": ", ".join(f.get("files", {}).values())} for f in results.get("figures", [])])
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df = df.map(lambda v: str(v) if isinstance(v, (list, dict)) else v)
            df.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            for c in ws[1]:
                c.fill = HEAD
                c.font = Font(bold=True, color="FFFFFF")
            ws.freeze_panes = "A2"
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(45, max(10, max(len(str(c.value or "")) for c in col[:50]) + 2))
    return path
