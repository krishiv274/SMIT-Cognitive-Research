"""Design diagrams (no data): task flow, temporal layout and stimulus illustrations."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

from ..experiment.config import ExperimentConfig  # noqa: E402

BLUE, ORANGE, GREY_BG = "#1F3A93", "#B35900", "#808080"


def _grid(ax, pattern, color, size=3, title=None, question=None):
    ax.set_facecolor(GREY_BG)
    ax.set_xlim(-0.5, size + 0.5)
    ax.set_ylim(-0.9, size + 0.9)
    ax.set_aspect("equal")
    ax.add_patch(mpatches.Rectangle((-0.08, -0.08), size + 0.16, size + 0.16, color="#404040"))
    for i in range(size * size):
        r, c = divmod(i, size)
        ax.add_patch(mpatches.Rectangle((c + 0.05, size - 1 - r + 0.05), 0.9, 0.9, color=color if i in pattern else "white"))
    if question:
        ax.text(size / 2, size + 0.45, question, ha="center", va="center", fontsize=7)
    ax.set_xticks([]); ax.set_yticks([])
    if title:
        ax.set_title(title, fontsize=9)
    for s in ax.spines.values():
        s.set_visible(False)


def stimulus_examples(path: Path) -> Path:
    fig, axes = plt.subplots(2, 4, figsize=(11, 5.6))
    panels = [
        ("1. Fixation (500 ms)", "fix"), ("2. Memory stimulus (500 ms)", ("grid", [0, 4, 5, 7], BLUE)),
        ("3A. Control: hold (3000 ms)", "dot"), ("3B. Numerical: verify (3000 ms)", "eq"),
        ("3C. Visual: symmetry? (3000 ms)", ("grid", [0, 2, 4, 7], ORANGE)), ("4. Retention (1000 ms)", "dot"),
        ("5a. Probe — SAME (F)", ("grid", [0, 4, 5, 7], BLUE)), ("5b. Probe — DIFFERENT (J)", ("grid", [0, 4, 5, 6], BLUE)),
    ]
    for ax, (title, kind) in zip(axes.flat, panels):
        if kind == "fix":
            ax.set_facecolor(GREY_BG); ax.text(0.5, 0.5, "+", fontsize=30, ha="center", va="center", transform=ax.transAxes)
        elif kind == "dot":
            ax.set_facecolor(GREY_BG); ax.plot([0.5], [0.5], "k.", ms=6, transform=ax.transAxes)
        elif kind == "eq":
            ax.set_facecolor(GREY_BG)
            ax.text(0.5, 0.75, "Is the equation correct?", ha="center", fontsize=8, transform=ax.transAxes)
            ax.text(0.5, 0.48, "7 + 6 = 13", ha="center", fontsize=18, weight="bold", transform=ax.transAxes)
            ax.text(0.5, 0.2, "F = True     J = False", ha="center", fontsize=8, transform=ax.transAxes)
        else:
            _, pat, col = kind
            _grid(ax, pat, col, question="Is the orange pattern symmetrical?" if col == ORANGE else None)
        ax.set_title(title, fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle("SMIT stimulus sequence (illustration; grids drawn at fixed central position, 110 px cells)", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def temporal_layout(path: Path, cfg: ExperimentConfig) -> Path:
    t = cfg.timing
    phases = [("Fixation", t.fixation_ms, "#BBBBBB"), ("Memory", t.memory_stimulus_ms, BLUE)]
    if t.post_stimulus_blank_ms:
        phases.append(("Blank", t.post_stimulus_blank_ms, "#DDDDDD"))
    phases += [("Interference (A: none / B: arithmetic / C: symmetry)", t.interference_ms, "#E69F00"),
               ("Retention", t.retention_ms, "#DDDDDD"), (f"Probe + response (≤ {t.recognition_deadline_ms})", t.recognition_deadline_ms, "#009E73"),
               (f"ITI {t.iti_min_ms}–{t.iti_max_ms} (jittered)", (t.iti_min_ms + t.iti_max_ms) / 2, "#F0F0F0")]
    fig, ax = plt.subplots(figsize=(12, 3.2))
    x = 0
    starts = {}
    for name, dur, col in phases:
        ax.add_patch(mpatches.Rectangle((x, 0.4), dur, 0.5, color=col, ec="black", lw=0.6))
        ax.text(x + dur / 2, 0.65, f"{name}\n{int(dur)} ms" if "ITI" not in name and "Probe" not in name else name,
                ha="center", va="center", fontsize=7.5, color="white" if col in (BLUE,) else "black")
        starts[name.split(" ")[0]] = x
        x += dur
    mem_on = starts["Memory"]
    probe_on = starts["Probe"]
    mem_off = mem_on + t.memory_stimulus_ms
    ax.annotate("", xy=(probe_on, 0.25), xytext=(mem_on, 0.25), arrowprops=dict(arrowstyle="<->"))
    ax.text((mem_on + probe_on) / 2, 0.13, f"SOA (memory → probe) = {int(probe_on - mem_on)} ms", ha="center", fontsize=8)
    ax.annotate("", xy=(probe_on, 1.05), xytext=(mem_off, 1.05), arrowprops=dict(arrowstyle="<->"))
    ax.text((mem_off + probe_on) / 2, 1.13, f"ISI (memory offset → probe onset) = {int(probe_on - mem_off)} ms", ha="center", fontsize=8)
    ax.set_xlim(-100, x + 100); ax.set_ylim(0, 1.3)
    ax.set_yticks([]); ax.set_xlabel("Time from trial onset (ms)")
    for s in ("left", "top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Temporal layout of one SMIT trial (lecture slide 13 terminology)")
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def task_flow(path: Path) -> Path:
    steps = ["Welcome", "Informed\nconsent", "Registration\n(ID generated)", "Instructions\n+ refresh check", "Practice\n6 trials + feedback",
             "Block 1\n20 trials", "Break\n≥ 20 s", "Block 2\n20 trials", "Break\n≥ 20 s", "Block 3\n20 trials", "Completion\n(ID, save check)"]
    fig, ax = plt.subplots(figsize=(13, 2.6))
    w, gap = 1.0, 0.25
    for i, s in enumerate(steps):
        x = i * (w + gap)
        col = "#DCE6F7" if "Block" in s else "#FFF1D6" if "Practice" in s else "#EEEEEE"
        ax.add_patch(mpatches.FancyBboxPatch((x, 0), w, 1, boxstyle="round,pad=0.03", fc=col, ec="#333333", lw=0.8))
        ax.text(x + w / 2, 0.5, s, ha="center", va="center", fontsize=7.5)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + w + gap, 0.5), xytext=(x + w, 0.5), arrowprops=dict(arrowstyle="->", lw=0.9))
    ax.text(0, -0.35, "Block order = one of ABC, ACB, BAC, BCA, CAB, CBA (persistent least-used assignment). "
                      "Trials saved after every trial; Esc → pause/withdraw; crash → resume from first unsaved trial.", fontsize=7.5)
    ax.set_xlim(-0.2, len(steps) * (w + gap)); ax.set_ylim(-0.5, 1.15)
    ax.axis("off")
    ax.set_title("Participant task flow")
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return path


def generate_all(out_dir: Path, cfg: ExperimentConfig) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    return {"stimuli": stimulus_examples(out_dir / "stimulus_sequence.png"),
            "temporal": temporal_layout(out_dir / "temporal_layout.png", cfg),
            "flow": task_flow(out_dir / "task_flow.png")}
