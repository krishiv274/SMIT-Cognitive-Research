# Theoretical Framework

## 1. The construct: visuospatial working memory

SMIT targets **visuospatial working memory (VSWM)**: the temporary maintenance of the spatial layout of a small set of locations over a delay of a few seconds. In the multi-component model this corresponds to the visuospatial sketchpad (Baddeley & Hitch, 1974; Logie, 1995), supervised by the central executive. In embedded-process and resource-sharing accounts it corresponds to a limited set of items kept active by attention (Cowan, 2001; Barrouillet et al., 2004).

SMIT also *involves* — but does not isolate or clinically measure — selective attention (choosing the blue memory grid over orange distractors), executive control (coordinating storage and processing), interference management, encoding, maintenance and recognition. Performance in SMIT is a behavioural composite of these processes.

## 2. Source paradigms

### 2.1 Visual change detection (Phillips, 1974; Pashler, 1988; Luck & Vogel, 1997)

*Principle borrowed:* brief presentation of an array → blank delay → test array → same/different decision. Accuracy reflects how much of the array was stored; with a whole-display probe, capacity can be estimated with Pashler's K (Rouder et al., 2011).

*How SMIT adapts it:* the "items" are four filled cells in a 3×3 matrix (a pattern-span-like stimulus; Della Sala et al., 1999); a *different* probe moves exactly one filled cell so that the number of filled cells is constant and only the spatial configuration changes (Jiang et al., 2000). The delay is much longer (4 s instead of ≈ 1 s) and is filled with a secondary task in two conditions.

### 2.2 Complex span (Daneman & Carpenter, 1980; Turner & Engle, 1989; Kane et al., 2004)

*Principle borrowed:* storage is tested after an intervening **processing** task, and processing accuracy is monitored to prevent participants from neglecting it (Conway et al., 2005; Unsworth et al., 2005).

*How SMIT adapts it:* one storage episode per trial instead of a list; processing is a single verification problem; the **type** of processing is the experimental manipulation (arithmetic as in operation span; symmetry judgement as in symmetry span); a no-processing control is included.

### 2.3 Selective-interference (dual-task) paradigm (Logie et al., 1990; Klauer & Zhao, 2004)

*Principle borrowed:* if a secondary task disrupts memory more when it shares the memory's domain, the two rely on overlapping resources.

*How SMIT adapts it:* compares a numerical secondary task with a visuospatial one, against a control, within subjects.

## 3. Causal model of a SMIT trial

```
Encoding (500 ms) ──► Consolidation ──► Maintenance (4,000 ms) ──► Comparison ──► Decision ──► Response (F/J)
                                              ▲
                     Condition B: arithmetic verification (central/verbal resources, attention capture)
                     Condition C: symmetry judgement on a competing spatial pattern
                                (visuospatial resources + attention capture + representational overlap)
```

Predicted mechanisms:

1. **Attentional capture (domain-general).** Any secondary task reduces the time available for attentional refreshing of the pattern (Barrouillet et al., 2004) and for spatial rehearsal through covert attention shifts (Awh et al., 1998) → lower accuracy in B and C than in A (H1, H2).
2. **Domain-specific competition.** The symmetry judgement requires building a representation of a second 3×3 spatial configuration in the *same* screen location. This competes with the sketchpad/inner-scribe resources and may overwrite or blend with the stored pattern (representational interference; Oberauer et al., 2016) → C < B (H3).
3. **Decision time.** A degraded trace may require more evidence before a decision (slower RT) or lead to guessing (faster RT near the deadline). H4 is therefore non-directional.

## 4. Lecture framework applied

The lecture's cognitive-task-design framework (goals/subgoals, cues/indicators, mental models, cognitive demands; *L3–L6*) and the attention networks (*L8–L10*) are applied explicitly in `Experimental_Design.md §5`. Temporal parameters (fixation, stimulus duration, ISI, SOA, ITI; *L13*) and timing thresholds (consolidation window, saccadic latency; *L15–L18*) determine the initial timings. Design-flaw controls (floor/ceiling, order effects, SAT, hardware latency; *L23–L28*) are built into the software and analysis plan.

## 5. Boundary conditions and construct-validity caveats

- The two secondary tasks differ in content **and** possibly in difficulty; a difference between B and C could reflect difficulty rather than domain. Secondary-task accuracy and RT are therefore recorded and compared, and the interpretation of H3 must take any difficulty difference into account.
- Condition A involves no response during the delay, so A–B and A–C differences combine cognitive load with motor/decision demands.
- Because the probe re-presents the whole pattern, participants may use a holistic "gestalt" comparison rather than item-by-item memory; capacity (K) estimates should be interpreted cautiously.
- The task measures recognition, not recall; recognition is generally easier and can be supported by familiarity.
