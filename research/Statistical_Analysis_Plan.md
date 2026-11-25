# Statistical Analysis Plan (SAP)

**Status:** Fixed before data collection. The numerical thresholds below are stored in the `analysis` section of the experiment configuration and are locked together with the configuration (version identifier recorded in every session). The analysis code in `backend/app/analysis/` implements exactly this plan.

## 1. Units of analysis

- The **participant** is the independent observational unit for all inferential tests. Trial-level data are aggregated to one value per participant per condition before testing. 1,200 trials from 20 participants are **never** treated as 1,200 independent observations.
- Trial-level data are used for descriptive summaries, data-quality checks and learning/fatigue plots only.

## 2. Data sources and scope

- Only **main-study** sessions are analysed. Pilot sessions (`session_type = pilot`) and practice trials (`practice_trial = true`) are excluded from all primary analyses.
- Data collected by the application and data uploaded via the Excel/CSV templates enter the same pipeline.
- Participant-summary-only imports (no trial-level data) contribute to participant-level analyses only; trial-level quality checks, timing checks, RT distributions, signal-detection measures and learning/fatigue analyses are unavailable for those participants and this is stated in the report.

## 3. Trial classification

Each experimental trial is classified into exactly one category:

| Category | Definition | Accuracy | RT |
|---|---|---|---|
| **Technically invalid** | Focus loss during the trial **or** memory-stimulus duration deviating from plan by more than 1 frame + 5 ms **or** any other phase deviating by > 50 ms **or** explicitly excluded by the researcher with a documented reason | Excluded | Excluded |
| **Missing response (timeout)** | No response within the 2,000 ms deadline | Counted as **incorrect** (primary); excluded from the "answered-only" sensitivity accuracy | Excluded |
| **Anticipatory** | Response < 200 ms after probe onset | Counted (as given) | Excluded (implausibly fast for a recognition decision) |
| **Incorrect** | Response given, wrong | Incorrect | Excluded (RT analyses use correct trials only) |
| **Correct** | Response given, right | Correct | Included if ≥ 200 ms |

Missing responses, incorrect responses and technically invalid trials are therefore distinguished throughout.

## 4. Participant-level exclusion rules (pre-specified)

A participant is excluded from the confirmatory analyses if **any** of the following holds. Every exclusion is listed with its reason in the report.

1. Withdrawn consent, or session not completed (fewer than the planned number of experimental trials recorded).
2. Fewer than **15 of 20** technically valid trials in any condition.
3. Timeout rate > **25 %** across experimental trials (non-engagement).
4. The same response key used on ≥ **90 %** of answered recognition trials (non-engagement / response bias).
5. Secondary-task accuracy < **60 %** in condition B or C (failure to engage with the interference manipulation, adapted from the processing-accuracy criterion used in complex-span research; Unsworth et al., 2005, used 85 %, which we relax because our secondary task is short and timed).
6. Excluded by the researcher with a documented reason (e.g., participant reported not understanding the task, severe interruption, equipment failure).

**Not** an exclusion criterion: low recognition accuracy. Poor performers who engaged with the task are retained, because excluding them on the basis of the primary outcome would bias the results.

## 5. Dependent variables (per participant × condition)

| Measure | Definition |
|---|---|
| Accuracy | correct ÷ valid trials (timeouts count as incorrect) |
| Accuracy (answered only) | correct ÷ valid answered trials (sensitivity analysis) |
| Error rate | 1 − accuracy |
| Timeout rate | timeouts ÷ valid trials |
| Mean / median correct RT | over correct, valid, non-anticipatory trials |
| Hit rate (H) | P("different" response \| different trial) |
| False-alarm rate (FA) | P("different" response \| same trial) |
| d′ | z(H) − z(FA), using the log-linear correction (add 0.5 to counts, 1 to totals; Hautus, 1995) |
| Pashler's K | N × (H − FA) / (1 − FA), N = 4 (whole-display probe; Rouder et al., 2011). Exploratory only, because the "items" are cell locations and the change is a location move |
| IES | mean correct RT ÷ accuracy; computed only if accuracy ≥ 0.60 in **every** condition for that participant, otherwise reported as unavailable (Bruyer & Brysbaert, 2011) |
| Secondary-task accuracy / RT | for conditions B and C, proportion of secondary items answered correctly (no response = incorrect) and mean RT of correct secondary responses |

### Interference costs (sign convention)

Costs are defined so that a **positive value always means worse performance under interference**:

- Numerical accuracy cost = Accuracy_A − Accuracy_B
- Visual accuracy cost = Accuracy_A − Accuracy_C
- Numerical RT cost = RT_B − RT_A (ms)
- Visual RT cost = RT_C − RT_A (ms)
- Mean interference cost = mean of the numerical and visual costs (used in exploratory correlations)

## 6. Descriptive statistics

For each DV, overall and by condition: n, mean, SD, median, minimum, maximum, IQR, and 95 % CI of the mean (t-distribution). Trial counts, accuracy, error rate, timeout rate, mean and median correct RT are also reported at the trial level (descriptive only).

## 7. Confirmatory analyses (H0–H4)

Performed separately for accuracy (H1–H3) and mean correct RT (H4).

### 7.1 Assumption checks

- Normality of each pairwise difference score (A−B, A−C, B−C): Shapiro–Wilk (α = .05) and Q–Q inspection.
- Sphericity: Mauchly's test; Greenhouse–Geisser ε is always reported.
- Ceiling check: proportion of participants at 100 % accuracy in each condition.

### 7.2 Omnibus test

- **Parametric route** (chosen if no difference score violates normality at α = .05): one-way repeated-measures ANOVA, F, df, p, partial η². If Mauchly's test is significant (p < .05), Greenhouse–Geisser-corrected df and p are reported as the primary result.
- **Nonparametric route** (chosen if any difference score violates normality, or if > 25 % of participants are at ceiling in any condition): Friedman test with Kendall's W.
- The test not chosen is still reported as a sensitivity analysis. The reason for the choice is printed in the results.

### 7.3 Pairwise comparisons

Three comparisons per DV: A vs B (H1), A vs C (H2), B vs C (H3 / H4 follow-up).

- Paired t-test (two-sided) with mean difference, 95 % CI, t, df, p, Cohen's d_z = mean difference / SD of differences, and Hedges-corrected g_z.
- Wilcoxon signed-rank test (two-sided) with rank-biserial correlation r_rb (Kerby, 2014).
- **Holm correction** across the three comparisons, separately for each DV and each test family. The primary test (t or Wilcoxon) follows the route chosen in 7.2.
- Pairwise comparisons are interpreted regardless of the omnibus result, because H1–H3 are planned contrasts; the omnibus result is reported for context.

### 7.4 Hypothesis decisions

| Hypothesis | Supported if |
|---|---|
| H1 | Holm-adjusted p < .05 for A vs B on accuracy **and** Accuracy_A > Accuracy_B |
| H2 | Holm-adjusted p < .05 for A vs C on accuracy **and** Accuracy_A > Accuracy_C |
| H3 | Holm-adjusted p < .05 for B vs C on accuracy **and** Accuracy_B > Accuracy_C |
| H4 | Omnibus test on mean correct RT significant at α = .05 (pairwise results describe where differences lie) |
| H0 (omnibus, accuracy) | Rejected if omnibus test on accuracy significant at α = .05 |

If a test is significant in the opposite direction, the hypothesis is reported as **not supported (effect in the opposite direction)**. The report always states that a non-significant result does not demonstrate the absence of an effect.

### 7.5 Manipulation check

Secondary-task accuracy and RT in B vs C are compared with a paired t-test / Wilcoxon (same rules). A significant difference indicates the two interference tasks were not matched in difficulty, which must be discussed when interpreting H3.

### 7.6 Sensitivity analyses

- Accuracy computed on answered trials only.
- Primary analyses repeated including participants flagged by exclusion rules 3–5 (if any).
- d′ analysed with the same omnibus/pairwise procedure (exploratory).

## 8. Exploratory analyses (RQ2)

- **Correlations** (participant level): age × overall accuracy; age × overall mean correct RT; age × mean accuracy cost; age × mean RT cost; overall accuracy × overall mean correct RT; plus a correlation matrix of numeric participant-level variables. Pearson's r is used when both variables pass Shapiro–Wilk (α = .05) and neither has fewer than 5 distinct values; otherwise Spearman's ρ. Reported: coefficient, 95 % CI (Fisher z; for ρ with the Bonett–Wright standard error), p, n. No multiplicity correction for exploratory correlations, which are labelled exploratory. Correlation ≠ causation.
- **Gender and course.** Nominal variables are never numerically coded as continuous variables. Groups with fewer than 5 participants are reported descriptively only. Two groups: Welch's t-test with Hedges' g, plus Mann–Whitney U with rank-biserial r. Three or more groups: Welch's ANOVA (ω²/η²) and Kruskal–Wallis (ε²). "Prefer not to answer" and missing categories are excluded from inferential comparisons and reported descriptively.
- **Order and fatigue.** Accuracy and RT by block position (1st/2nd/3rd) — Friedman/RM-ANOVA with the same rules — and accuracy/RT across trial number within blocks (descriptive plot).
- **Condition order.** Descriptive comparison of performance across the six counterbalancing orders (groups too small for inference with N ≈ 20).

## 9. Power and sample size

With N = 20, a two-sided paired t-test at α = .05 has 80 % power for d_z ≥ 0.66; at the strictest Holm level (α = .0167) for d_z ≥ 0.78 (computed with statsmodels `TTestPower`). Detecting d_z = 0.5 with 80 % power would require ≈ 34 participants. The study is therefore powered only for medium-to-large effects; this is stated as a limitation.

## 10. Software

Python: pandas, NumPy, SciPy, statsmodels (power, multiple testing), Pingouin (cross-checks), Matplotlib (figures). Every analysis run stores the dataset hash, configuration versions, software versions, exclusion log and the full results JSON (`analysis_runs` table), so results can be reproduced.

## 11. Deviations

Any deviation from this plan after data collection (e.g., an unforeseen data problem) must be documented in the report's "Deviations from the analysis plan" section, with the reason and the result of the planned analysis alongside the deviating one.
