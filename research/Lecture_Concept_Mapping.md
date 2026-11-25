# Mapping of Design Decisions to the Week 14 Lecture

Source: `CognitivePsychology_Week14_All.pdf` ("Week 14 — Cognitive Task Designing", 28 slides). *L-n* = PDF page/slide *n*. Slides 7 ("Let's understand from an example of ANT") and 14 ("Temporal layout of cognitive tasks") contain only a title in the exported PDF; their content is therefore not cited.

**Evidence type key**

- **[Lecture]** — concept or value stated directly in the lecture.
- **[Literature]** — supported by additional peer-reviewed literature (see `Literature_Review.md`).
- **[Design]** — independently proposed design decision by the project team, justified but not taken from a source.

## 1. Slide inventory

| Slide | Content |
|---|---|
| L1–L2 | Title: Week 14 Cognitive Task Designing; Task designing |
| L3 | Cognitive task components: goals & subgoals, cues & indicators, mental models, cognitive demands |
| L4 | Flow diagram: observe environment cues → access mental model → simulate/predict outcome → execute action → evaluate feedback (adjust strategy / refine framework) |
| L5 | Definition of mental model ("cognitive blueprint", "brain's simulator") |
| L6 | How mental models drive action: information filtering; simulation & prediction; action & remediation |
| L7 | Example of ANT (title only) |
| L8 | Alerting network — temporal expectations from a warning cue |
| L9 | Orienting network — spatial map, covert spatial attention |
| L10 | Executive network — conflict resolution, filtering rule ("flankers are noise") |
| L11 | Possible errors from an inaccurate mental model |
| L12 | Day 2 |
| L13 | Essential components: fixation, stimulus duration (< 200 ms prevents saccades), ISI, SOA = Stimulus 1 duration + ISI, ITI jittered 800–1200 ms |
| L14 | Temporal layout of cognitive tasks (title only) |
| L15 | Recurrent processing & visual awareness threshold ≈ 30–50 ms |
| L16 | Saccadic latency ≈ 180–200 ms; covert vs overt attention |
| L17 | Working-memory consolidation window 200–500 ms; shorter exposures vulnerable to retroactive interference |
| L18 | Table of stimulus-duration ranges: mid-range 200–500 ms → working-memory encoding, change-detection target exposure; ≥ 2000 ms → WM rehearsal, n-back delay maintenance, fatigue |
| L19 | Selective attention / interference: IV congruency, DVs RT and error rate; keep target–distractor spacing constant |
| L20 | Sustained attention: rare targets |
| L21 | Working memory paradigms: complex span (processing + encoding alternate), n-back |
| L22 | Inhibitory function: Go/No-Go, Stop-signal |
| L23 | Common design flaws: floor/ceiling (chance 50 %, 100 %) → pilot testing; order effects & fatigue → counterbalancing with Latin square or complete randomisation |
| L24 | Speed–accuracy trade-off → IES = Mean RT / Accuracy rate, or response deadlines; hardware latency 15–50 ms → wired peripherals, log refresh rate (60 Hz = 16.67 ms/frame), avoid variable system clocks |
| L25 | Technical inputs: refresh-rate limits, exposure timing, SAT |
| L26 | Frame duration = 1000 / refresh rate; durations must be integer multiples of a frame; 144 Hz = 6.94 ms |
| L27 | Exposure too short (16 ms) → floor at 50 %; too long (3000 ms per item) → ceiling via mnemonic strategies |
| L28 | SAT curve; short durations push participants down the SAT curve |

## 2. Concept-to-design mapping

| Concept | Slide(s) | How it is applied in SMIT | Evidence |
|---|---|---|---|
| Goals and subgoals | L3 | Per-phase goal table (encode → maintain + secondary task → compare → respond); instructions state the overall goal | [Lecture] + [Design] |
| Cues and indicators | L3, L4 | Fixation cross; blue memory/probe grids; orange distractor grid; question text and key reminders; block instruction and break screens | [Lecture] + [Design] |
| Mental model | L4, L5 | Instructions and practice build the rules: "only blue matters", "exactly one square moves", "F = same/true, J = different/false" | [Lecture] |
| Information filtering | L6 | Colour coding tells participants which grid to store and which to ignore | [Lecture] + [Design] |
| Simulation and prediction | L4, L6 | Fixed trial structure lets participants anticipate the sequence (but jittered ITI prevents anticipation of exact onset) | [Lecture] |
| Action and remediation | L4, L6, L11 | Practice feedback lets participants correct a faulty model; repeat-practice option | [Lecture] + [Design] |
| Inaccurate mental models | L11 | Faulty model ("compare against the orange grid") anticipated and countered by colour coding, instructions and practice | [Lecture] + [Design] |
| Cognitive demands | L3 | Encoding, maintenance, interference resistance, recognition, response selection analysed per phase | [Lecture] |
| Alerting network | L8 | 500 ms fixation acts as a warning cue with a fixed fixation→stimulus interval | [Lecture] + [Literature] (Posner & Petersen, 1990; Fan et al., 2002) |
| Orienting network | L9 | All stimuli at a fixed central location; orienting demands are minimised rather than manipulated | [Lecture] + [Design] |
| Executive network | L10 | Conditions B and C require coordinating secondary processing with maintenance and ignoring the orange distractor | [Lecture] + [Literature] (Kane et al., 2004) |
| Fixation | L13 | 500 ms central "+" before every memory stimulus | [Lecture] |
| Stimulus duration | L13, L16, L17, L18 | 500 ms memory exposure: within the 200–500 ms consolidation / change-detection exposure range; > 200 ms so overt scanning is possible | [Lecture] + [Literature] (Vogel et al., 2006) |
| ISI | L13 | Memory offset → probe onset = 4,000 ms (default); logged per trial | [Lecture] |
| SOA | L13 | SOA = stimulus duration + ISI = 4,500 ms (memory → probe); 500 ms (memory → secondary stimulus) | [Lecture] |
| ITI | L13 | Jittered uniformly 800–1,200 ms (the lecture's example) | [Lecture] |
| Working-memory consolidation | L17 | Exposure ≥ 200 ms; optional post-stimulus blank to protect consolidation is configurable for pilot testing | [Lecture] + [Literature] (Jolicœur & Dell'Acqua, 1998) |
| Maintenance / sustained range | L18 | 4 s delay falls in the ≥ 2,000 ms "working memory rehearsal / delay maintenance" range | [Lecture] |
| Selective attention / interference | L19 | IV = interference type (analogous to congruency levels), DVs = RT and error rate; distractor grid at the same spatial position as the memory grid (constant spacing) | [Lecture] + [Design] |
| Complex Span paradigm | L21 | Processing (arithmetic / symmetry) between encoding and test; processing accuracy recorded | [Lecture] + [Literature] (Turner & Engle, 1989; Kane et al., 2004) |
| Change Detection paradigm | L18 | Memory array → delay → probe → same/different judgement | [Lecture] + [Literature] (Luck & Vogel, 1997) |
| Floor and ceiling effects | L23, L27 | Set size 4 (near capacity); configurable exposure, set size, interference duration, change type and deadline; pilot criteria; ceiling check in analysis | [Lecture] + [Literature] (Cowan, 2001) |
| Order effects | L23 | Complete counterbalancing of block order across 6 orders; block-position analysis | [Lecture] |
| Fatigue effects | L18, L23 | Short session (≈ 15–20 min), standardised breaks, fatigue trend analysis | [Lecture] |
| Counterbalancing | L23 | Persistent least-used assignment of the 6 orders | [Lecture] + [Design] |
| Latin Square design | L23 | For 3 conditions, the 6 orders form a balanced (Williams-type) Latin-square set; complete counterbalancing used | [Lecture] |
| Speed–accuracy trade-off | L24, L28 | Accuracy and RT analysed separately; 2,000 ms deadline; accuracy–RT correlation | [Lecture] + [Literature] (Heitz, 2014) |
| Inverse Efficiency Score | L24 | IES = mean correct RT / proportion correct, computed only when accuracy ≥ 60 % in all conditions | [Lecture] + [Literature] (Bruyer & Brysbaert, 2011) |
| Hardware latency | L24 | Recommend same machine and wired keyboard; event timestamps on the high-resolution clock; limitations stated | [Lecture] + [Literature] (Anwyl-Irvine et al., 2021) |
| Monitor refresh-rate limitations | L24, L26 | Refresh rate estimated and logged; durations converted to whole frames; actual durations recorded | [Lecture] |
| Avoid variable system clocks | L24 | `performance.now()` / frame timestamps instead of `Date.now()` | [Lecture] |
| Pilot testing | L23, L27 | Human pilot-testing protocol and checklist; pilot mode isolated from main data | [Lecture] + [Design] |
| Exposure timing calibration | L25, L27 | Pilot protocol specifies how to adjust exposure/set size if pilot accuracy is near floor or ceiling | [Lecture] |
| Recurrent processing threshold | L15 | Not manipulated; all stimuli are far above 30–50 ms, so they are consciously perceived | [Lecture] |
| Sustained attention, Go/No-Go, Stop-signal, n-back | L20–L22 | Not used: not relevant to the research question (listed for completeness, not forced into the design) | [Lecture] |
