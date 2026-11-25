# Experimental Design — SMIT (Spatial Memory Interference Task)

**Full title:** Investigating the Effects of Numerical and Visual Interference on Spatial Working Memory and Cognitive Performance Among University Students

Slide references (e.g. *L13*) point to page numbers of the lecture deck `CognitivePsychology_Week14_All.pdf`. See `Lecture_Concept_Mapping.md` for the full mapping.

---

## 1. Design overview

| Feature | Decision |
|---|---|
| Design | One-factor, three-level **within-subjects (repeated-measures)** design |
| Independent variable | Interference condition during retention: **A** Control, **B** Numerical, **C** Visual |
| Primary dependent variables | Recognition accuracy (proportion correct); mean correct recognition RT (ms) |
| Task type | Delayed **recognition** (same/different change detection) of a spatial pattern — *not free recall* |
| Trials | 6 practice (2 per condition, with feedback) + 60 experimental (20 per condition; 10 same + 10 different per condition) |
| Blocking | Conditions are presented in blocks; trial order is randomised within each block |
| Counterbalancing | All 6 permutations of block order (ABC, ACB, BAC, BCA, CAB, CBA), assigned persistently with a least-used rule |
| Target sample | ≥ 20 eligible adult participants (≥ 18 years) who complete the experiment |
| Estimated duration | ≈ 15–20 minutes including instructions, practice and breaks |

### Why within-subjects?

Each participant serves as their own control, which removes between-person variability in baseline spatial memory capacity from the condition comparison. This greatly increases statistical power for the small (N ≈ 20) sample required by the assignment. The cost — order, practice and fatigue effects (*L23*) — is controlled by full counterbalancing of block order and by standardised breaks.

### Why blocked rather than intermixed conditions?

Blocking lets participants form a stable mental model of the secondary task for each block (*L5–L6*), reduces task-switching costs that would otherwise contaminate the interference effect, and allows a single instruction screen per condition. The disadvantage (condition is confounded with time within a session) is addressed by counterbalancing block order across participants.

---

## 2. Trial sequence and temporal layout

| # | Stage | Planned duration | Screen content | Purpose |
|---|---|---:|---|---|
| 1 | Fixation | 500 ms | Central black "+" on grey background | Centre gaze and reset spatial attention (*L13*); warning signal for the alerting network (*L8*) |
| 2 | Memory stimulus | 500 ms | 3×3 grid, 4 cells filled dark blue | Encode the spatial pattern; 500 ms lies at the upper end of the working-memory consolidation window of 200–500 ms (*L17, L18*) |
| 3 | (Optional) post-stimulus blank | 0 ms (configurable) | Blank grey | Allows a consolidation gap to be introduced during pilot testing if needed |
| 4 | Interference phase | 3,000 ms (fixed) | **A:** blank screen with small central dot. **B:** arithmetic equation (e.g. `7 + 6 = 13`). **C:** a new 3×3 grid with 4 orange cells; judge left–right symmetry | Manipulate the cognitive load during maintenance |
| 5 | Retention interval | 1,000 ms | Blank grey with small central dot | Further maintenance; separates the secondary response from the recognition decision |
| 6 | Recognition probe + response | until response, max 2,000 ms | 3×3 grid, 4 cells filled dark blue | Same/different decision: **F = Same, J = Different** |
| 7 | Inter-trial interval (ITI) | jittered uniformly 800–1,200 ms | Blank grey | Prevents temporal anticipation (*L13*) |

The interference phase always lasts exactly 3,000 ms, regardless of how quickly the secondary-task response is made, so that the retention interval is identical across conditions. After a secondary response the secondary stimulus is removed and replaced by the central dot until the phase ends.

### Temporal parameters defined in the lecture (*L13*)

With the default timings:

| Parameter | Definition | Value in SMIT |
|---|---|---|
| Stimulus duration | Time the memory pattern is visible | 500 ms (30 frames at 60 Hz) |
| ISI (memory → probe) | Offset of memory stimulus to onset of recognition probe | 0 + 3,000 + 1,000 = **4,000 ms** |
| SOA (memory → probe) | Onset of memory stimulus to onset of probe = stimulus duration + ISI | 500 + 4,000 = **4,500 ms** |
| SOA (memory → secondary stimulus) | Onset of memory stimulus to onset of interference stimulus | **500 ms** (ISI = 0 ms) |
| ITI | End of one trial to fixation of the next | **800–1,200 ms, jittered** (exactly the lecture example) |

```
time (ms) 0      500     1000                           4000          5000       ≤7000     +800..1200
          |--FIX--|--MEM--|------ INTERFERENCE (3000) ------|--RETENTION--|--PROBE+RESP--|----ITI----|
                  ^ onset S1                                              ^ onset S2
                  |<----------------------- SOA = 4500 ms --------------->|
                          |<------------------ ISI = 4000 ms ------------>|
```

A rendered version of this diagram (`temporal_layout.png/svg`) is produced by `scripts/generate_design_figures.py` and included in the report.

### Justification of initial timings

- **Fixation 500 ms.** Long enough to fixate centrally and act as a temporal warning cue (alerting network, *L8*), short enough not to induce vigilance decrement.
- **Memory exposure 500 ms.** The lecture places working-memory encoding/change-detection exposure in the 200–500 ms "temporal bottleneck" range (*L18*) and states consolidation takes ≈ 200–500 ms (*L17*); shorter exposures leave traces vulnerable to retroactive interference. This is consistent with Vogel et al. (2006), who showed that visual working-memory consolidation takes time and is vulnerable to masking shortly after offset. 500 ms is above the ≈ 200 ms saccadic latency (*L16*), so overt scanning of a small central grid is possible; this is acceptable because the grid is compact (≈ 350 px) and we are not attempting to measure covert attention. The duration is kept well below the 3,000 ms per item that the lecture warns produces ceiling effects through elaborate mnemonic strategies (*L27*).
- **Interference 3,000 ms.** Long enough to present and respond to a simple verification problem (typical verification RTs ≈ 1–2 s), creating a maintenance period in the "sustained" range (≥ 2,000 ms) associated with working-memory rehearsal (*L18*).
- **Retention 1,000 ms.** Separates the secondary-task motor response from the recognition decision, reducing response-conflict carry-over because both tasks use the F/J keys.
- **Response deadline 2,000 ms.** Prevents very slow, strategic responding and limits the speed–accuracy trade-off (*L24*: "enforce response deadlines").
- **ITI 800–1,200 ms jittered.** Taken directly from the lecture example (*L13*).

**All values are initial design parameters.** They are configurable in the researcher dashboard (pilot mode) and must be calibrated in human pilot testing (see `experiment/documentation/Pilot_Testing_Protocol.md`) before the configuration is locked.

---

## 3. Stimuli

### Memory and recognition grids

- 3×3 grid of white cells (110 × 110 px, 10 px gaps) on a uniform mid-grey (#808080) background, centred on the screen and drawn on an HTML canvas at a fixed position for every trial.
- Exactly **4 of the 9 cells** are filled dark blue (#1F3A93). 4 items is close to the typical visual working-memory capacity of ≈ 3–4 items (Luck & Vogel, 1997; Cowan, 2001), which should avoid both floor and ceiling effects (*L23, L27*). The set size is configurable.
- There are C(9,4) = 126 possible patterns. Each session draws **66 distinct patterns without replacement** (6 practice + 60 experimental), so no pattern is repeated within a participant.
- **Same trials:** the probe is identical to the memory pattern.
- **Different trials:** exactly one filled cell is moved to a previously unfilled position. The probe therefore always contains the same number (4) of filled cells, so the change cannot be detected by counting.
- Recognition difficulty is configurable via `change_type`: `any` (default; any empty cell), `adjacent` (moved cell lands next to its original position — harder) or `non_adjacent` (easier).

### Secondary (interference) stimuli

Both secondary tasks are **binary true/false verification tasks** using the same keys (**F = True/Yes, J = False/No**), presented centrally, with a 50 % "true" rate and the same 3,000 ms window, to match response demands as closely as possible.

| Condition | Stimulus | Question | Engaged processes |
|---|---|---|---|
| B — Numerical | Single-digit addition equation, e.g. `7 + 6 = 13` (operands 2–9; false answers differ by ±1 or ±2) | "Is the equation correct?" | Arithmetic retrieval/verification; verbal/central-executive resources |
| C — Visual | A new 3×3 grid with 4 **orange** filled cells | "Is the pattern symmetrical (left–right mirror)?" | Visuospatial processing of a competing spatial configuration in the same screen location |

The symmetry judgement is modelled on the processing component of the **symmetry span** task (Kane et al., 2004), an established visuospatial complex-span task, but scaled down to a 3×3 grid so that its difficulty is closer to single-digit addition verification. A "centre-cell" probe ("Is the centre square filled?") is available as a configurable alternative (`secondary_tasks.visual.probe = "centre"`).

**Independence from the memory task.** The visual distractor pattern is generated independently of the memory pattern and of whether the trial is *same* or *different*; it is never identical to either the memory pattern or the probe. Therefore the distractor carries no systematic information about the correct recognition response. (By construction, the expected overlap between distractor and memory pattern is 4 × 4 / 9 ≈ 1.8 cells for both same and different trials; the unit tests verify this.)

The control condition (A) contains **no secondary task**: a blank screen with a small central dot is shown for 3,000 ms. Consequently, condition A differs from B and C both in cognitive load and in the requirement to make an extra response; this is an acknowledged limitation (see Research Protocol §Limitations).

---

## 4. Trial structure, randomisation and counterbalancing

- **Practice (6 trials):** two trials per condition in a fixed order (A, A, B, B, C, C) with the corresponding instruction screen before each pair, and correctness feedback ("Correct", "Incorrect", "Too slow") after every trial, including secondary-task feedback. Participants may repeat the practice up to two times. Practice data are stored with `practice_trial = true` and excluded from all primary analyses.
- **Experimental blocks (60 trials):** three blocks of 20 trials (one per condition). Within each block: exactly 10 same and 10 different trials, randomly ordered with no more than 3 consecutive trials with the same correct answer (prevents runs that encourage response-pattern guessing). Exactly 10 numerical equations are true and 10 false; exactly 10 visual distractors are symmetric and 10 asymmetric.
- **No feedback** is given during experimental trials, so that performance knowledge cannot change strategy or motivation differently across conditions, and no running score is displayed.
- **Breaks:** a standardised break screen of at least 20 s (configurable) between blocks, followed by the instruction screen for the next condition.
- **Counterbalancing:** all six possible orders of the three conditions (complete counterbalancing, which for three conditions is equivalent to a balanced Latin-square set of 2 × 3 rows) are used. Each new main-study session receives the order with the fewest previously assigned *non-withdrawn* main sessions (ties broken in the fixed order ABC, ACB, BAC, BCA, CAB, CBA). Assignment is stored in the database, so it is persistent and reproducible. With 24 participants each order would be used exactly 4 times; with 20 participants, orders are used 3 or 4 times.
- **Reproducibility:** each session stores a random seed. The complete trial plan (patterns, probe changes, secondary stimuli, ITIs) is generated deterministically by the server from the locked configuration, the seed and the condition order, and is also stored verbatim with the session.

---

## 5. Cognitive task components (*L3*)

### Goals and subgoals

| Phase | Participant goal / subgoal |
|---|---|
| Fixation | Look at the centre and get ready (prepare for the stimulus) |
| Memory stimulus | Encode the locations of the 4 blue cells as a single spatial configuration |
| Interference — A | Maintain (rehearse) the pattern without any other demand |
| Interference — B/C | Quickly and accurately verify the equation / symmetry **while** keeping the blue pattern in mind |
| Retention | Re-focus on the stored pattern |
| Recognition | Compare the probe to memory and decide *same* or *different* as quickly and accurately as possible |
| Overall goal | Maximise correct same/different decisions within the deadline while also performing the secondary task |

### Cues and indicators

- **Fixation cross (+)** — signals trial onset and that the memory stimulus is imminent (temporal warning cue, *L8*).
- **Blue grid** — the to-be-remembered stimulus (memory) or the probe (recognition). Using the same blue colour for both and a different (orange) colour for the visual distractor is an *information-filtering* cue telling the participant which grid matters for the memory task (*L6*).
- **Interference prompt** — the equation or orange grid with the question text and key reminder "F = True · J = False".
- **Response cue** — appearance of the blue probe grid with the reminder "F = Same · J = Different" below it.
- **Break and block instruction screens** — indicate which secondary task the next block contains.
- **Practice feedback** — "Correct / Incorrect / Too slow", used only during practice to correct faulty mental models (*L4, L11*).

### Mental model

To perform well the participant must hold the following internal rules (the task's mental model, *L5*):

1. "Only the **blue** grid has to be remembered; orange grids and equations are a separate job."
2. "The second blue grid either is identical or has **exactly one** square moved — the number of squares never changes, so counting does not help."
3. "During the middle phase I must answer the equation/symmetry question **and** keep the blue pattern in mind."
4. "F always means *same / true*, J always means *different / false*."
5. "I have about 2 seconds to answer; if I wait too long the trial is lost."

The lecture describes how an inaccurate mental model produces systematic errors (*L11*). In SMIT a plausible faulty model is "orange grids may be the pattern to compare against" — this is why the distractor uses a different colour and why practice gives explicit feedback. The model also supports **simulation & prediction** (expecting the probe after the delay) and **action & remediation** (feedback in practice allows the model to be adjusted, *L4, L6*).

### Cognitive demands (bottlenecks)

| Demand | Where | Expected bottleneck |
|---|---|---|
| Encoding / consolidation | Memory stimulus (500 ms) | Limited consolidation time for 4 locations (*L17*) |
| Maintenance | Interference + retention (4 s) | Decay/refreshing; rehearsal competes with secondary task |
| Interference resistance (executive control) | B and C | Sharing attention between processing and storage; protecting the trace from a competing spatial pattern in C (*L10, L19*) |
| Recognition (comparison) | Probe | Comparing probe and memory; deciding under uncertainty |
| Response selection | Probe | Mapping decision to F/J under a deadline; potential response conflict from the secondary F/J response |

---

## 6. Design threats and controls

### Floor and ceiling effects (*L23, L27*)

Configurable levers: `grid.highlight_count`, `timing.memory_stimulus_ms`, `timing.interference_ms`, `trials.change_type` (recognition difficulty) and `timing.recognition_deadline_ms`. Pilot criteria (see Pilot Testing Protocol): control-condition accuracy should fall roughly between 70 % and 92 % for most pilot participants, and no condition should average near chance (50 %).

### Order effects and fatigue (*L23*)

Complete counterbalancing of block order; standardised breaks; short session (≈ 15–20 min); exploratory analysis of performance by block position and trial number.

### Speed–accuracy trade-off (*L24, L28*)

Accuracy and RT are analysed separately; a response deadline is enforced; Inverse Efficiency Score (IES = mean correct RT / proportion correct) is computed as a supplementary measure only when accuracy ≥ 60 % in every condition, because IES is unstable and misleading at low accuracy (Bruyer & Brysbaert, 2011).

### Hardware and timing (*L24, L26*)

- The browser's refresh rate is estimated at session start (median of ≈ 60 animation-frame intervals) and stored with the session.
- Stimulus changes are synchronised to `requestAnimationFrame`; planned durations are converted to whole numbers of frames (e.g. 500 ms = 30 frames at 60 Hz). Non-integer multiples (e.g. 500 ms at 75 Hz = 37.5 frames) are rounded to the nearest frame and the actual duration is recorded.
- For every phase the **measured** duration (frame timestamps) is stored alongside the planned duration; deviations beyond one frame + 5 ms for the memory stimulus mark the trial as technically invalid.
- Window blur / tab hiding (focus loss) is detected and flagged per trial; browser background-tab throttling would otherwise distort timing.
- Keyboard events use `event.timeStamp` (high-resolution, same clock as frame timestamps); auto-repeat events and keypresses outside the response window are ignored and counted.
- Testing should use the same desktop/laptop, monitor and **wired** keyboard for all participants (Bluetooth keyboards add ≈ 15–50 ms latency, *L24*), in full-screen mode, with other applications closed.
- Browser-based timing is not laboratory-grade; published benchmarks show typical browser timing variability of a few to tens of milliseconds depending on platform (Anwyl-Irvine et al., 2021; Bridges et al., 2020). The project therefore does **not** claim laboratory-grade precision, and between-condition comparisons rely on all conditions sharing the same hardware within participants.
