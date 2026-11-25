# SMIT — Viva Preparation

Questions you are likely to be asked, with scientifically accurate answers. Slide numbers (*L-n*) refer to the Week 14 lecture PDF. Answers about **results** must be written by you after the analysis — never memorise results before they exist.

---

## A. Cognitive tasks and paradigms

**1. What is a cognitive task?**
A standardised procedure that presents controlled stimuli and records behavioural responses (accuracy, reaction time) to infer an underlying cognitive process. The lecture frames a task in terms of goals/subgoals, cues/indicators, mental models and cognitive demands (*L3*). SMIT's process of interest is visuospatial working memory.

**2. What is an experimental paradigm?**
An established, reusable task structure with known properties and a body of literature — e.g. change detection, complex span, n-back, Stroop, flanker. A paradigm fixes the logic (what is manipulated, what is measured); individual studies choose its parameters.

**3. Why did you choose this framework?**
Change detection gives a clean, brief test of how much spatial information is held (Luck & Vogel, 1997), and complex span shows how a processing task during retention loads working memory (Turner & Engle, 1989; Kane et al., 2004). Combining them lets us manipulate the *type* of processing during the delay while measuring recognition of the same spatial material — exactly what the research question needs.

**4. What makes the proposed task distinctive?**
It is an adaptation, not a new paradigm. Distinctive features: (a) a within-subjects comparison of a no-load control, an arithmetic task and a spatial symmetry task in the *same* delay; (b) both secondary tasks share response format, keys, timing window and 50 % true rate; (c) the visual distractor is generated independently of the memory and probe patterns so it cannot cue the answer; (d) the "different" probe moves exactly one cell, so counting cannot solve the task; (e) every phase is frame-synchronised and its actual duration logged. We do not claim that no similar task exists.

**5. What cognitive ability are you measuring?**
Primarily visuospatial working memory — encoding, maintaining and recognising a spatial configuration. Performance also depends on selective attention and executive control (sharing attention between storage and processing), but the task does not isolate or clinically measure those.

## B. Timing and trial structure

**6. Why did you choose these stimulus timings?**
Fixation 500 ms is a warning cue (alerting network, *L8*). Memory exposure 500 ms falls in the 200–500 ms working-memory consolidation window and the change-detection exposure range (*L17–L18*) — long enough to consolidate, far shorter than the 3,000 ms that encourages mnemonic strategies and ceiling effects (*L27*). The 3 s interference phase is long enough to answer a verification problem; the total 4 s delay sits in the ≥ 2,000 ms maintenance range (*L18*). The 2 s deadline limits speed–accuracy trade-offs (*L24*). The ITI is jittered 800–1,200 ms as in the lecture (*L13*). All are initial values to be calibrated by human piloting.

**7. What is fixation?**
A central point (+) shown before the stimulus to centre gaze and reset spatial attention (*L13*); it also tells the participant that a trial is about to start.

**8. What are ISI, SOA and ITI?**
ISI is the interval between the offset of one stimulus and the onset of the next within a trial; SOA is the time from the onset of stimulus 1 to the onset of stimulus 2 (SOA = stimulus-1 duration + ISI); ITI is the interval between the end of one trial and the start of the next (*L13*). In SMIT: ISI memory→probe = 4,000 ms; SOA = 500 + 4,000 = 4,500 ms; ITI = 800–1,200 ms jittered.

**9. Why jitter the ITI?**
So participants cannot predict exactly when the next trial starts; anticipatory timing would otherwise speed RTs artificially (*L13*).

**10. How did you handle monitor refresh rate?**
Frame duration = 1000 / refresh rate (16.67 ms at 60 Hz; *L26*). The app estimates the refresh rate, converts each planned duration to whole frames, changes the display only on animation frames, and logs the measured duration of every phase. A 500 ms stimulus is exactly 30 frames at 60 Hz; on a 75 Hz monitor it is rounded to 37 or 38 frames and the actual value is stored.

## C. Mental models and attention

**11. What is a mental model?**
An internal representation of how a system works that lets a person filter information, predict outcomes and correct errors (*L5–L6*). In SMIT the participant's model is: "only the blue grid is remembered; exactly one square may move; F = same/true, J = different/false; answer within 2 s."

**12. What happens if a participant's mental model is wrong?**
Behaviour changes systematically (*L11*) — e.g. if someone compared the probe with the orange grid, accuracy in condition C would collapse. That is why we use distinct colours, explicit instructions, practice with feedback and a repeat-practice option.

**13. Which attention networks are involved?**
Alerting (fixation as warning cue), orienting (minimised: everything appears at the same central location), and executive control (managing the secondary task while protecting the memory; ignoring the orange distractor) (*L8–L10*; Posner & Petersen, 1990).

## D. Interference, recall and recognition

**14. What is interference?**
Disruption of a target representation or response by competing information or processing. Here, a secondary task during the retention interval competes with maintenance of the spatial pattern. Domain-specific theories predict more disruption when the secondary task uses the same (visuospatial) resources; domain-general theories predict disruption proportional to attentional load (Barrouillet et al., 2004).

**15. What is the difference between recall and recognition?**
Recall requires reproducing the information (e.g. clicking the remembered cells); recognition requires judging whether a presented item matches memory. SMIT measures delayed recognition (same/different). Recognition is usually easier and can be supported by familiarity, so it may underestimate memory differences.

## E. Design

**16. What is the independent variable?**
Interference condition: A control, B numerical, C visual — manipulated within subjects.

**17. What are the dependent variables?**
Recognition accuracy (proportion correct, timeouts counted as errors) and mean correct reaction time. Secondary DVs: timeout rate, d′, capacity K, IES, interference costs; secondary-task accuracy is a manipulation check.

**18. Why use a within-subjects design?**
Each participant is their own control, removing stable individual differences in memory capacity from the comparison and giving much more power with ~20 participants. The cost is order/practice/fatigue effects, which we counterbalance.

**19. Why counterbalance condition order?**
Performance changes over a session through learning and fatigue (*L23*). If every participant did A first, condition would be confounded with time. Using all six orders equally often spreads these effects across conditions.

**20. What is a Latin square, and did you use one?**
A design in which each condition appears once in each position across a set of orders. With three conditions, a balanced (Williams) design needs six orders, which equals all permutations; we used all six (complete counterbalancing), assigned with a persistent least-used rule.

**21. What are floor and ceiling effects?**
If a task is too hard, scores cluster near chance (50 % here); too easy, near 100 %. Either way, differences between conditions and people are hidden (*L23, L27*). We chose set size 4 (near capacity), made exposure, set size, change type, interference duration and deadline configurable, check ceiling in the analysis, and calibrate in the pilot.

**22. Why did you include practice trials and why exclude them from analysis?**
Practice builds the correct mental model and reduces early learning effects; its data reflect learning the task rather than the steady-state ability, so it is excluded.

## F. Speed–accuracy and efficiency

**23. What is the speed–accuracy trade-off?**
People can respond faster by accepting more errors, or slower to be more accurate (*L24, L28*). A condition could look "better" on RT only because accuracy dropped. We therefore analyse accuracy and RT separately, enforce a deadline and inspect the accuracy–RT association.

**24. What is the Inverse Efficiency Score?**
IES = mean correct RT / proportion correct (*L24*). It combines speed and accuracy into one number (higher = less efficient). It is only meaningful when accuracy is high and similar across conditions; with low accuracy it becomes unstable (Bruyer & Brysbaert, 2011), so we compute it only when accuracy ≥ 60 % in all conditions and treat it as supplementary.

## G. Statistics

**25. Why use paired t-tests?**
Each participant contributes a score in every condition, so scores are dependent. The paired t-test analyses within-person differences and removes between-person variance. We use three planned comparisons with Holm correction and switch to Wilcoxon signed-rank tests if differences are not normally distributed.

**26. Why use repeated-measures ANOVA?**
To test whether any of the three conditions differ in one omnibus test while accounting for repeated measurement. Its sphericity assumption is checked with Mauchly's test; if violated, the Greenhouse–Geisser correction is applied. If normality fails, the Friedman test is used.

**27. What is statistical significance?**
A result is "significant" when, assuming the null hypothesis were true, data at least this extreme would be unlikely (p < α = .05). It is not the probability that the hypothesis is true, says nothing about the size or importance of the effect, and a non-significant result does not prove there is no effect.

**28. What is an effect size, and which did you use?**
A standardised measure of how large an effect is, independent of sample size. We report Cohen's d_z for paired comparisons, partial η² for the ANOVA, rank-biserial r for Wilcoxon, Kendall's W for Friedman, r/ρ for correlations and Hedges' g for group comparisons.

**29. Why apply the Holm correction?**
Running several tests inflates the chance of at least one false positive. Holm's sequential procedure controls the family-wise error rate and is uniformly more powerful than Bonferroni.

**30. Why does correlation not imply causation?**
An association between, say, age and accuracy may be due to a third variable (e.g. course or experience), reverse causation, or chance, and age is not manipulated. Only the interference manipulation (randomised order, within subjects) supports causal claims about interference.

**31. Why is the participant, not the trial, the unit of analysis?**
Trials from the same person are not independent. Treating 1,200 trials as 1,200 observations would massively overstate precision (pseudo-replication). We average within participant and condition, then test across participants.

**32. How big a sample do you need?**
With N = 20, a paired test has 80 % power for d_z ≥ 0.66 at α = .05; detecting d_z = 0.5 would need ≈ 34 people. Our study can detect medium-to-large effects only — a limitation we report.

## H. Hardware, data and limitations

**33. How did you account for hardware limitations?**
Same desktop/laptop and wired keyboard for everyone (Bluetooth adds 15–50 ms, *L24*); full-screen mode; refresh-rate estimate; frame-synchronised presentation; high-resolution timestamps instead of system clock (*L24*); logging of measured durations, dropped frames and focus loss; pre-specified rules that exclude technically invalid trials. We do not claim lab-grade timing (Anwyl-Irvine et al., 2021).

**34. How did you protect participant privacy?**
Pseudonymous IDs; email stored in a separate table, never in exports, analyses or reports; contact access audit-logged; data stored locally; withdrawal/deletion supported; no third-party services.

**35. What is the difference between pilot testing and your automated tests?**
Automated tests verify the software (timing logic, data storage, statistics) using synthetic data. Human pilot testing checks whether real people understand the task and whether difficulty avoids floor/ceiling. Only the latter can calibrate the task; we do not present software tests as pilot testing.

**36. What are the limitations of your task?**
Small convenience sample; narrow age range; browser timing; possibly unequal secondary-task difficulty; control condition lacks a secondary response; recognition may rely on familiarity; shared response keys may cause carry-over; one set size and timing configuration limit generalisation.

**37. Why might visual interference not differ from numerical interference?**
If both tasks capture attention equally (domain-general account), or if the symmetry task is quick enough to leave time for refreshing, or the sample lacks power, or performance is near ceiling.

**38. What would you change in a follow-up study?**
Calibrate secondary-task difficulty individually (as in automated OSpan; Unsworth et al., 2005); add a control with a neutral response; vary set size to estimate capacity; preregister; larger and more diverse sample; lab-grade timing hardware.

---

### After data collection, prepare answers to:

- What were your main results (means, test, p, effect size)?
- Which hypotheses were supported, and how confident are you?
- Did the secondary tasks differ in difficulty (manipulation check)?
- Were there exclusions, and why?
- Any ceiling effects or order effects?
