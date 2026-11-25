# Stimuli

Stimuli are generated procedurally at run time (no image files are shown to participants):

| Stimulus | Specification (default configuration) |
|---|---|
| Fixation | black "+" (28 px, 3 px stroke) at screen centre on mid-grey #808080 |
| Memory / probe grid | 3×3 white cells (110 px, 10 px gaps, dark-grey frame), 4 cells filled #1F3A93 (blue), centred |
| Visual distractor | same grid geometry, 4 cells filled #B35900 (orange); symmetric (left–right mirror) on 50 % of trials, otherwise "near-symmetric" (one cell away from a symmetric pattern) |
| Equation | `a + b = c`, a, b ∈ 2–9; c correct on 50 % of trials, otherwise off by ±1 or ±2; 56 px text |
| Hold / retention | blank grey with 3 px central dot |
| Key reminders | "F = Same · J = Different" under the probe; "F = True · J = False" / "F = Yes · J = No" during interference |

Rendering code: `frontend/src/engine/renderer.ts`. Generation logic: `backend/app/experiment/plan.py`.
The PNG files here are **illustrations** for documentation and the report (regenerate with `scripts/generate_preliminary_deliverables.py`).
