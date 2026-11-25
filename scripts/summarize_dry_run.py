"""Summarise tests/artifacts/dry_run_session.json (timing of the automated full-length dry run) as Markdown."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
d = json.loads((Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests/artifacts/dry_run_session.json").read_text())
s = d["session"]
tr = [t for t in d["trials"]]
main = [t for t in tr if not t["practice"]]
print(f"- Refresh rate detected: {s['estimated_refresh_rate']} Hz; screen {s['screen_information']}; trials: {len(main)} experimental + {len(tr) - len(main)} practice")
print(f"- Timing flags (all trials): {d['flags']}")
print("\n| Phase | Planned (ms) | n | Mean measured | SD | Min | Max | Mean |dev| | Max |dev| | Trials within ±1 frame |")
print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
frame = 1000 / (s["estimated_refresh_rate"] or 60)
for key, planned, label in (("fix", 500, "Fixation"), ("mem", 500, "Memory stimulus"), ("int", 3000, "Interference"), ("ret", 1000, "Retention")):
    v = np.array([t[key] for t in tr if t[key] is not None], float)
    dev = v - planned
    within = np.mean(np.abs(dev) <= frame + 0.5) * 100
    print(f"| {label} | {planned} | {len(v)} | {v.mean():.1f} | {v.std(ddof=1):.2f} | {v.min():.1f} | {v.max():.1f} | {np.abs(dev).mean():.2f} | {np.abs(dev).max():.1f} | {within:.1f}% |")
iti = np.array([t["iti"] - t["planned_iti"] for t in tr if t["iti"] is not None], float)
print(f"| ITI (measured − planned jittered value) | 800–1200 | {len(iti)} | {iti.mean():+.1f} | {iti.std(ddof=1):.2f} | {iti.min():+.1f} | {iti.max():+.1f} | — | — | — |")
rts = [t["rt"] for t in main if t["rt"] is not None]
print(f"\n- Recognition responses recorded: {len(rts)}/{len(main)}; automated key presses were scheduled ~350–710 ms after detecting probe onset; recorded RT range {min(rts):.0f}–{max(rts):.0f} ms")
print(f"- Secondary responses recorded on {sum(t['sec'] is not None for t in main if t['cond'] != 'A')}/{sum(t['cond'] != 'A' for t in main)} interference trials")
print(f"- Dropped-frame events: {sum((t['dropped'] or 0) for t in tr)} across {sum(1 for t in tr if t['dropped'])} trials")
