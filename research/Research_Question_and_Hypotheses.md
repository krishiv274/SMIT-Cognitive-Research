# Research Questions and Hypotheses

**Project:** SMIT — Spatial Memory Interference Task
**Status:** Pre-specified before any participant data were collected. These hypotheses must not be modified after genuine participant results have been viewed. Any later change must be recorded as a deviation in the final report.

## Primary (confirmatory) research question

> **RQ1.** How do different types of cognitive interference (none, numerical, visual-spatial) presented during the retention interval affect spatial working memory *recognition accuracy* and *recognition reaction time* among university students?

The wording of the original project brief was refined in one respect only: "interference" is specified as interference *presented during the retention interval*, because that is the manipulation actually implemented (the secondary task is performed after the memory pattern disappears and before the recognition probe appears).

## Secondary (exploratory) research question

> **RQ2.** How does spatial working memory performance vary with age, gender and academic course, and what relationships exist between recognition accuracy, recognition reaction time and interference-related performance costs?

RQ2 is exploratory. No directional demographic predictions are made, because (a) the expected sample (≈20 university students) has a restricted age range, (b) gender and course groups are likely to be small and unbalanced, and (c) there is no strong theoretical basis for directional predictions in this population for this specific task.

## Variables

| Role | Variable | Levels / units | Notes |
|---|---|---|---|
| Independent variable (within-subjects) | Interference condition | A = Control (no secondary task); B = Numerical interference (arithmetic verification); C = Visual interference (spatial symmetry judgement) | Every participant completes all three conditions in a counterbalanced block order |
| Primary DV 1 | Recognition accuracy | Proportion correct (0–1) | Timeouts are counted as errors in the primary accuracy measure (see Statistical Analysis Plan) |
| Primary DV 2 | Mean correct recognition RT | Milliseconds | Correct, non-anticipatory (≥ 200 ms), technically valid trials only |
| Secondary DVs | Timeout rate, hit rate, false-alarm rate, d′, Pashler's K, Inverse Efficiency Score (IES), interference costs | See Statistical Analysis Plan | Exploratory / descriptive |
| Manipulation check | Secondary-task accuracy and RT (conditions B and C) | Proportion correct, ms | Used to verify engagement with the interference task |
| Exploratory predictors | Age (years), gender (category), academic course (category) | — | Nominal variables are never numerically coded and treated as continuous |
| Controlled variables | Grid geometry, set size (4 highlighted cells), stimulus timings, response keys, trial counts, same/different balance | — | Fixed by the locked experiment configuration |
| Counterbalancing factor | Condition order (ABC, ACB, BAC, BCA, CAB, CBA) | 6 orders | Assigned persistently to balance order across participants |

## Hypotheses

All tests are evaluated at α = .05 (two-sided), with Holm correction across the three pairwise comparisons for each dependent variable. A directional hypothesis is considered **supported** only if the corrected test is statistically significant **and** the effect is in the predicted direction.

### Omnibus null hypothesis

- **H0 (omnibus):** Interference type has no effect on spatial memory recognition performance. Formally, population mean recognition accuracy is equal across conditions A, B and C (μ_A = μ_B = μ_C), and likewise for mean correct recognition RT.
- **H0 alternative (omnibus):** At least one condition mean differs from the others.

### Specific hypotheses

| ID | Alternative hypothesis (H₁) | Null hypothesis (H₀) | Test |
|---|---|---|---|
| **H1** | Numerical interference reduces recognition accuracy relative to control (μ_B < μ_A). | μ_A = μ_B | Paired comparison A vs B on accuracy |
| **H2** | Visual interference reduces recognition accuracy relative to control (μ_C < μ_A). | μ_A = μ_C | Paired comparison A vs C on accuracy |
| **H3** | Visual interference produces greater spatial memory disruption than numerical interference (μ_C < μ_B on accuracy). | μ_B = μ_C | Paired comparison B vs C on accuracy |
| **H4** | Interference affects recognition reaction time (mean correct RT differs between at least one interference condition and control). | μ_RT,A = μ_RT,B = μ_RT,C | Repeated-measures ANOVA (or Friedman) on mean correct RT, followed by Holm-corrected pairwise comparisons |

### Theoretical rationale (summary)

- **H1 and H2** follow from resource-sharing and time-based accounts of working memory (Barrouillet et al., 2004) and from complex-span research showing that a processing task performed during retention reduces storage performance (Daneman & Carpenter, 1980; Turner & Engle, 1989; Conway et al., 2005). Any attention-demanding secondary task is expected to reduce the opportunity for attentional refreshing/rehearsal of the spatial pattern (Awh et al., 1998).
- **H3** follows from domain-specific (multi-component) models of working memory, in which a visuospatial secondary task competes for the same visuospatial resources as the stored pattern, whereas arithmetic draws more heavily on verbal/central resources (Baddeley & Hitch, 1974; Logie, 1995; Shah & Miyake, 1996; Klauer & Zhao, 2004). Note that domain-general accounts (e.g., Morey & Cowan, 2004; Cocchini et al., 2002 found evidence for both) would predict smaller or no differences between B and C if the two tasks are equally demanding — which is why secondary-task difficulty is measured.
- **H4** is non-directional because interference may slow recognition (weaker memory trace → longer decision time) or speed it (lower confidence → faster guessing near the deadline). The speed–accuracy trade-off is therefore examined explicitly.

### Exploratory analyses (RQ2) — no confirmatory hypotheses

- Correlations: age vs overall accuracy; age vs overall mean correct RT; age vs interference costs; accuracy vs RT (across participants).
- Group comparisons by gender and academic course, only where each group has at least 5 participants (configurable); otherwise descriptive statistics only.
- Order/fatigue: accuracy and RT by block position (1st, 2nd, 3rd) and trial number.

## Interpretation rules (pre-specified)

1. A non-significant result is reported as "no statistically significant evidence of a difference", **never** as evidence that no effect exists.
2. Effect sizes (paired Cohen's d_z, partial η², rank-biserial r, Kendall's W) and 95% confidence intervals are always reported with p-values.
3. Correlations are interpreted as associations only, never as causal effects.
4. With N ≈ 20, a two-sided paired t-test has 80% power only for effects of d_z ≥ 0.66 at α = .05 (d_z ≥ 0.78 at the Holm-adjusted α = .0167 for the smallest p-value). Smaller true effects may not be detected.
