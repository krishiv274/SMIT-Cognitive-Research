"""SMIT_Presentation.pptx (python-pptx). Data-dependent slides are filled from an
analysis run when one with eligible data exists, otherwise marked as pending."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

from ..experiment.config import ExperimentConfig
from ..settings import REPO_ROOT
from .builder import COND, TITLE, pct, pe

BLUE = RGBColor(0x1F, 0x3A, 0x93)
AMBER = RGBColor(0xB3, 0x59, 0x00)
PENDING = "PENDING — will be generated from genuine participant data (click 'Regenerate presentation' after analysis)."


class Deck:
    def __init__(self):
        self.p = Presentation()
        self.p.slide_width, self.p.slide_height = Inches(13.333), Inches(7.5)
        self.n = 0

    def slide(self, title: str, bullets: list[str] | None = None, image: Path | None = None, note: str | None = None,
              pending: bool = False, img_left: bool = False):
        self.n += 1
        s = self.p.slides.add_slide(self.p.slide_layouts[5])
        t = s.shapes.title
        t.text = title
        t.left, t.top, t.width, t.height = Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0)
        for para in t.text_frame.paragraphs:
            for r in para.runs:
                r.font.size, r.font.bold, r.font.color.rgb = Pt(30), True, BLUE
        has_img = image is not None and image.exists()
        tw = Inches(6.2) if has_img else Inches(12.3)
        if bullets:
            box = s.shapes.add_textbox(Inches(0.6) if not (has_img and img_left) else Inches(6.9), Inches(1.45), tw, Inches(5.4))
            tf = box.text_frame
            tf.word_wrap = True
            for i, b in enumerate(bullets):
                para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                sub = b.startswith("  ")
                para.text = ("– " if sub else "• ") + b.strip()
                para.level = 1 if sub else 0
                para.space_after = Pt(6)
                for r in para.runs:
                    r.font.size = Pt(15 if sub else 18)
                    if pending:
                        r.font.color.rgb = AMBER
                        r.font.italic = True
        if has_img:
            from PIL import Image as PILImage  # pillow is a matplotlib dependency

            with PILImage.open(image) as im:
                w, h = im.size
            maxw, maxh = (Inches(6.0), Inches(5.5)) if bullets else (Inches(12.0), Inches(5.6))
            scale = min(maxw / w, maxh / h)
            left = Inches(0.6) if (img_left or not bullets) else Inches(6.95)
            if not bullets:
                left = Emu(int((self.p.slide_width - w * scale) / 2))
            s.shapes.add_picture(str(image), left, Inches(1.5), width=Emu(int(w * scale)), height=Emu(int(h * scale)))
        foot = s.shapes.add_textbox(Inches(0.5), Inches(7.0), Inches(12.3), Inches(0.4)).text_frame
        foot.text = f"SMIT — Spatial Memory Interference Task   |   {self.n}"
        foot.paragraphs[0].runs[0].font.size = Pt(10)
        foot.paragraphs[0].runs[0].font.color.rgb = RGBColor(0x66, 0x66, 0x66)
        if note:
            s.notes_slide.notes_text_frame.text = note
        return s


def build_presentation(path: Path, cfg: ExperimentConfig, settings: dict, results: dict | None, figdir: Path | None) -> Path:
    final = bool(results and results["meta"]["status"] == "ok")
    t = cfg.timing
    stim = REPO_ROOT / "experiment" / "stimuli"
    d = Deck()
    s = d.slide("SMIT — Spatial Memory Interference Task", [TITLE, f"{settings.get('student_names', '')}",
                f"{settings.get('course_name', '')} · {settings.get('university_name', '')}",
                "FINAL (results from analysed data — review required)" if final else "PRELIMINARY — results pending genuine data collection"])
    d.slide("1. Project introduction", ["Spatial working memory: holding where things are for a few seconds",
            "Everyday memory is rarely undisturbed — we calculate, read and look at other displays",
            "SMIT asks whether the TYPE of concurrent activity matters for spatial memory",
            "Custom adaptation of change detection + complex span (not a new paradigm)"])
    d.slide("2. Research problem", ["Domain-specific models: interference depends on content overlap (Logie et al., 1990; Klauer & Zhao, 2004)",
            "Domain-general models: interference depends on attentional load (Barrouillet et al., 2004)",
            "Does visual interference disrupt spatial memory more than numerical interference?"])
    d.slide("3. Cognitive ability investigated", ["Primary: visuospatial working memory (encoding, maintenance, recognition)",
            "Also involved (not isolated): selective attention, executive control, interference management",
            "Outcome = delayed RECOGNITION (same/different), not free recall"])
    d.slide("4. Theoretical framework", ["Change detection (Phillips, 1974; Luck & Vogel, 1997): array → delay → probe",
            "Complex span (Turner & Engle, 1989; Kane et al., 2004): processing between encoding and retrieval",
            "Selective interference (Logie et al., 1990): compare content of secondary tasks",
            "Multi-component model (Baddeley & Hitch, 1974); embedded processes (Cowan, 2001)"])
    d.slide("5. The proposed cognitive task", ["3×3 grid, 4 blue cells, 500 ms", "3 s interference phase: none / arithmetic / symmetry",
            "1 s retention, then probe: same or one cell moved (F/J)", "60 trials, 20 per condition, 10 same + 10 different"], stim / "stimulus_sequence.png")
    d.slide("6. Goals, cues, mental model, cognitive demands", ["Goal: correct same/different decision; subgoals per phase (encode, maintain, verify, compare)",
            "Cues: fixation cross, blue vs orange colour coding, key reminders", "Mental model: 'only blue matters, exactly one square moves, F = same/true'",
            "Demands: consolidation, maintenance under load, interference resistance, response selection under a deadline"],
            note="Lecture slides 3–6, 8–11.")
    d.slide("7. Experimental conditions", ["A Control: blank 3 s hold", "B Numerical: verify e.g. 7 + 6 = 13 (F true / J false)",
            "C Visual: is the orange pattern symmetrical? (F yes / J no)", "Secondary tasks matched in format, timing, 50% true; accuracy recorded"])
    d.slide("8. Stimulus timing", [f"Fixation {t.fixation_ms} · memory {t.memory_stimulus_ms} · interference {t.interference_ms} · retention {t.retention_ms} ms",
            f"Response deadline {t.recognition_deadline_ms} ms; ITI {t.iti_min_ms}–{t.iti_max_ms} ms jittered",
            "Memory exposure within 200–500 ms consolidation window (lecture slide 17)", "Durations rounded to whole frames; actual durations logged"],
            stim / "temporal_layout.png")
    d.slide("9. Experimental variables", ["IV: interference condition (within subjects)", "DVs: accuracy (proportion correct), mean correct RT",
            "Secondary: timeouts, d′, K, IES, interference costs; manipulation check: secondary accuracy",
            "Exploratory: age, gender, course; controlled: grid, set size, timings, keys"])
    d.slide("10. Research question", ["RQ1: How do numerical and visual interference affect spatial working-memory recognition accuracy and RT?",
            "RQ2 (exploratory): variation with age, gender, course; relations between accuracy, RT and interference costs"])
    d.slide("11. Hypotheses", ["H0: interference type has no effect", "H1: numerical < control (accuracy)", "H2: visual < control (accuracy)",
            "H3: visual < numerical (accuracy)", "H4: interference affects RT", "Fixed before data collection; demographics exploratory"])
    d.slide("12. Counterbalancing", ["All 6 block orders (ABC … CBA) — complete counterbalancing / balanced Latin square for 3 conditions",
            "Persistent least-used assignment, stored in the database", "Random seeds → reproducible trial plans", "Breaks ≥ 20 s between blocks"],
            stim / "task_flow.png")
    d.slide("13. Pilot-testing methodology", ["Automated dry run: unit, integration, end-to-end and timing tests (software only)",
            "Human pilot: 3–5 volunteers, same hardware; calibrate floor/ceiling (control accuracy ≈ 70–92%)",
            "Check secondary-task accuracy, timeouts, timing deviations", "Then lock configuration with a version ID",
            ("Pilot observations: " + settings["pilot_observations"][:200]) if settings.get("pilot_observations") else "  Human pilot observations: pending"])
    d.slide("14. Data collection", ["≥ 20 adult university students; informed consent", "Same computer, wired keyboard, full screen",
            "Trial data saved after every trial; email stored separately", "External data: Excel/CSV template → validated upload"])
    d.slide("15. Statistical analysis", ["Participant = unit of analysis", "RM-ANOVA (Mauchly, Greenhouse–Geisser) or Friedman, chosen by pre-specified rules",
            "Paired t / Wilcoxon with Holm correction; d_z, ηp², r_rb", "Exploratory correlations with 95% CIs; Welch tests for groups ≥ 5"])
    # data-dependent slides
    if final:
        m = results["meta"]
        acc = results["confirmatory"]["accuracy"]
        desc = results["descriptives"]["accuracy"]
        fig1 = (figdir / "01_accuracy_by_condition.png") if figdir else None
        d.slide("16. Results", [f"N = {m['n_included']} eligible ({m['n_excluded']} excluded)",
                                *[f"{COND[c]}: {pct(desc[c]['mean'])} correct" for c in "ABC"],
                                f"Omnibus ({acc['omnibus']['test']}): {pe(acc['omnibus']['p'])}"] +
                [f"{h['id']}: {h['decision']}" for h in results["hypotheses"] if h["id"] != "H0"], fig1,
                note="Auto-generated from analysis results; verify before presenting.")
        fig2 = (figdir / "02_rt_by_condition.png") if figdir else None
        rt = results["confirmatory"]["rt"]
        d.slide("16b. Results — reaction time and costs", [f"RT omnibus: {pe(rt['omnibus']['p']) if rt.get('status') == 'ok' else 'n/a'}",
                "Interference costs: positive = worse than control", "See report for full tables and effect sizes"], fig2)
        d.slide("17. Discussion", [f"{h['id']}: {h['decision']}" for h in results["hypotheses"]] +
                ["Interpretation must consider secondary-task difficulty (manipulation check)", "[Authors: add your interpretation]"],
                note="Draft — the team must write and approve the interpretation.")
    else:
        d.slide("16. Actual results", [PENDING], pending=True)
        d.slide("17. Discussion", [PENDING], pending=True)
    d.slide("18. Limitations", ["Small convenience sample (power only for d_z ≥ 0.66)", "Narrow age range; unbalanced demographic groups",
            "Browser timing is not laboratory-grade", "Secondary tasks may differ in difficulty", "Control condition has no secondary response",
            "Practice/fatigue effects reduced, not eliminated"])
    if final:
        sup = [h["id"] for h in results["hypotheses"] if h["decision"] == "supported"]
        d.slide("19. Conclusion", [("Supported: " + ", ".join(sup)) if sup else "No directional hypothesis supported",
                                   "Associations under the tested parameters; not causal claims beyond the manipulation", "[Authors: final take-home message]"])
    else:
        d.slide("19. Conclusion", [PENDING], pending=True)
    d.slide("20. References (selection)", ["Baddeley & Hitch (1974); Baddeley (2000, 2012)", "Luck & Vogel (1997); Cowan (2001); Rouder et al. (2011)",
            "Turner & Engle (1989); Kane et al. (2004); Conway et al. (2005); Unsworth et al. (2005)",
            "Logie et al. (1990); Klauer & Zhao (2004); Cocchini et al. (2002); Morey & Cowan (2004)",
            "Barrouillet et al. (2004); Vogel et al. (2006); Bruyer & Brysbaert (2011); Anwyl-Irvine et al. (2021)",
            "Full APA 7 list in the research report"])
    path.parent.mkdir(parents=True, exist_ok=True)
    d.p.save(str(path))
    return path
