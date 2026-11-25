"""Timing-quality assessment shared by live collection, import and analysis."""
from __future__ import annotations

from ..experiment.config import AnalysisConfig

DEFAULT_REFRESH_HZ = 60.0


def frame_ms(refresh_hz: float | None) -> float:
    if not refresh_hz or refresh_hz < 20 or refresh_hz > 500:
        refresh_hz = DEFAULT_REFRESH_HZ
    return 1000.0 / refresh_hz


def assess_timing(trial: dict, refresh_hz: float | None, acfg: AnalysisConfig) -> tuple[str, str | None]:
    """Return (flag, notes) where flag is 'ok' | 'warning' | 'invalid'.

    Rules (Statistical Analysis Plan §3):
      * focus loss during the trial -> invalid
      * |measured - planned| memory stimulus > N frames + extra ms -> invalid
      * any other phase deviating by > max_other_phase_deviation_ms -> invalid
      * any other phase deviating by more than 1 frame + extra ms -> warning
    Phases without a measured duration (e.g. imported data without timing
    columns) cannot be assessed and are noted, not penalised.
    """
    notes: list[str] = []
    flag = "ok"
    fr = frame_ms(refresh_hz)

    if trial.get("focus_loss"):
        return "invalid", "focus loss during trial"

    def dev(planned_key: str, measured_key: str) -> float | None:
        p, m = trial.get(planned_key), trial.get(measured_key)
        if p is None or m is None:
            return None
        return float(m) - float(p)

    mem = dev("planned_stimulus_duration_ms", "measured_stimulus_duration_ms")
    mem_tol = acfg.max_memory_stimulus_deviation_frames * fr + acfg.timing_tolerance_extra_ms
    if mem is None:
        notes.append("memory stimulus duration not measured")
    elif abs(mem) > mem_tol:
        flag = "invalid"
        notes.append(f"memory stimulus deviated {mem:+.1f} ms (tolerance ±{mem_tol:.1f})")

    warn_tol = fr + acfg.timing_tolerance_extra_ms
    for name, pk, mk in (
        ("fixation", "planned_fixation_duration_ms", "actual_fixation_duration_ms"),
        ("interference", "planned_interference_duration_ms", "measured_interference_duration_ms"),
        ("retention", "planned_retention_duration_ms", "measured_retention_duration_ms"),
    ):
        d = dev(pk, mk)
        if d is None:
            continue
        if abs(d) > acfg.max_other_phase_deviation_ms:
            flag = "invalid"
            notes.append(f"{name} deviated {d:+.1f} ms")
        elif abs(d) > warn_tol and flag == "ok":
            flag = "warning"
            notes.append(f"{name} deviated {d:+.1f} ms")
    dropped = trial.get("dropped_frames")
    if dropped and flag == "ok":
        flag = "warning"
        notes.append(f"{dropped} long frame interval(s) detected")
    return flag, ("; ".join(notes) or None)
