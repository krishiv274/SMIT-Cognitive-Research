# Human Pilot-Testing Protocol

**Purpose.** Pilot testing checks that the task works for real people and calibrates difficulty before the configuration is locked (*L23, L27*). Software tests (`pilot/Technical_Dry_Run_Report.md`) are **not** human pilot testing and must never be reported as such.

**Who.** 3–5 volunteers similar to the target population (adult university students) who will **not** take part in the main study. Pilot data are stored with `session_type = pilot` and are excluded from all main analyses automatically.

## Procedure

1. In the researcher dashboard open **Configuration**, review the draft configuration and save any changes as a new draft version.
2. Open **Pilot Mode** and click **Start pilot session**. The participant view opens in a new tab with a pilot banner (the banner is visible only to the researcher before the task starts; it is not shown during trials).
3. Use the same computer, monitor, wired keyboard, room and lighting planned for the main study. Close other applications and disable notifications.
4. Read the instructions aloud with the volunteer if needed and observe them silently during the task. Note anything confusing.
5. After the session, ask the debrief questions in `pilot/Human_Pilot_Testing_Checklist.xlsx` (sheet *Debrief*).
6. In **Pilot Mode → Session details**, inspect the timing table: planned vs measured durations, refresh-rate estimate, dropped-frame warnings and focus-loss flags.
7. Record observations in the checklist and in the dashboard (**Settings → Pilot observations**), which feed the report's "Pilot testing" section.

## Calibration criteria

| Check | Target | If not met |
|---|---|---|
| Control (A) accuracy | Most volunteers between ≈ 70 % and 92 % | > 92 % (ceiling): increase `highlight_count` to 5, or reduce `memory_stimulus_ms` to 300–400 ms, or use `change_type = adjacent`. < 65 % (near floor): reduce set size to 3, increase exposure (max 1,000 ms), or use `change_type = non_adjacent` |
| Interference conditions (B, C) | Mean accuracy clearly above 50 % (chance) | Reduce `interference_ms` or secondary difficulty |
| Secondary task accuracy (B, C) | ≥ 85 % on average; similar for B and C | If one task is much harder, adjust operand range (B) or switch visual probe (`symmetry` ↔ `centre`) |
| Secondary task RT | Answer typically given within 3 s; similar B vs C | Adjust difficulty as above |
| Timeouts on recognition | < 10 % | Consider 2,500 ms deadline |
| Measured memory stimulus duration | Within ± 1 frame of plan on ≥ 95 % of trials | Use a different browser (Chrome/Edge recommended), close background apps, use the built-in display, disable power saving |
| Refresh rate | Stable (e.g. 60 Hz) | Fix display settings; do not mix devices |
| Instructions | Volunteer can explain the rules back | Edit instruction wording |
| Duration | ≤ 20 min | Shorten breaks |

Adjust **one parameter at a time**, re-pilot with at least one new volunteer, and document every change and its reason (the dashboard keeps an audit log of configuration versions).

## Locking

When the criteria are met, open **Configuration → Lock for main study**, enter a justification, and confirm. The configuration receives a permanent version identifier (e.g. `SMIT-1.0.0-3fa2c1d9`). Main-study sessions can only run with a locked configuration, and every session records the version it used. Changing parameters after locking requires creating a new version, which is recorded in the audit log and must be reported as a deviation.
