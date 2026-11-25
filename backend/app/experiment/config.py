"""Validated experiment configuration schema.

The JSON stored in ``experiment_configs.config_json`` must validate against
:class:`ExperimentConfig`. Hashing uses canonical (sorted-key) JSON so the same
parameters always produce the same version identifier.
"""
from __future__ import annotations

import hashlib
import json
from math import comb
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class GridConfig(BaseModel):
    size: int = Field(3, ge=3, le=5, description="Grid is size x size cells")
    highlight_count: int = Field(4, ge=2, le=8)
    cell_size_px: int = Field(110, ge=40, le=200)
    cell_gap_px: int = Field(10, ge=0, le=40)
    background_color: str = "#808080"
    cell_color: str = "#FFFFFF"
    memory_highlight_color: str = "#1F3A93"
    visual_interference_highlight_color: str = "#B35900"
    grid_border_color: str = "#404040"

    @model_validator(mode="after")
    def _check(self) -> "GridConfig":
        if self.highlight_count >= self.size * self.size:
            raise ValueError("highlight_count must be smaller than the number of cells")
        for f in ("background_color", "cell_color", "memory_highlight_color",
                  "visual_interference_highlight_color", "grid_border_color"):
            v = getattr(self, f)
            if not (isinstance(v, str) and v.startswith("#") and len(v) in (4, 7)):
                raise ValueError(f"{f} must be a hex colour like #RRGGBB")
        return self


class TimingConfig(BaseModel):
    fixation_ms: int = Field(500, ge=100, le=3000)
    memory_stimulus_ms: int = Field(500, ge=50, le=5000)
    post_stimulus_blank_ms: int = Field(0, ge=0, le=3000)
    interference_ms: int = Field(3000, ge=500, le=10000)
    retention_ms: int = Field(1000, ge=0, le=10000)
    recognition_deadline_ms: int = Field(2000, ge=500, le=10000)
    iti_min_ms: int = Field(800, ge=0, le=5000)
    iti_max_ms: int = Field(1200, ge=0, le=5000)
    practice_feedback_ms: int = Field(1500, ge=300, le=5000)
    break_min_s: int = Field(20, ge=0, le=600)

    @model_validator(mode="after")
    def _check(self) -> "TimingConfig":
        if self.iti_max_ms < self.iti_min_ms:
            raise ValueError("iti_max_ms must be >= iti_min_ms")
        return self


class TrialsConfig(BaseModel):
    practice_per_condition: int = Field(2, ge=0, le=10)
    trials_per_condition: int = Field(20, ge=2, le=100)
    same_proportion: float = Field(0.5, gt=0, lt=1)
    max_same_answer_run: int = Field(3, ge=2, le=20)
    change_type: Literal["any", "adjacent", "non_adjacent"] = "any"
    max_practice_repeats: int = Field(2, ge=0, le=5)

    @model_validator(mode="after")
    def _check(self) -> "TrialsConfig":
        n_same = self.trials_per_condition * self.same_proportion
        if abs(n_same - round(n_same)) > 1e-9:
            raise ValueError("trials_per_condition * same_proportion must be a whole number")
        return self


class NumericalTaskConfig(BaseModel):
    operand_min: int = Field(2, ge=0, le=50)
    operand_max: int = Field(9, ge=1, le=99)
    operation: Literal["addition"] = "addition"
    false_offsets: list[int] = Field(default_factory=lambda: [-2, -1, 1, 2])
    true_proportion: float = Field(0.5, gt=0, lt=1)

    @field_validator("false_offsets")
    @classmethod
    def _offsets(cls, v: list[int]) -> list[int]:
        if not v or any(o == 0 for o in v):
            raise ValueError("false_offsets must be non-empty and non-zero")
        return v

    @model_validator(mode="after")
    def _check(self) -> "NumericalTaskConfig":
        if self.operand_max < self.operand_min:
            raise ValueError("operand_max must be >= operand_min")
        return self


class VisualTaskConfig(BaseModel):
    probe: Literal["symmetry", "centre"] = "symmetry"
    highlight_count: int = Field(4, ge=1, le=8)
    true_proportion: float = Field(0.5, gt=0, lt=1)


class SecondaryTasksConfig(BaseModel):
    numerical: NumericalTaskConfig = Field(default_factory=NumericalTaskConfig)
    visual: VisualTaskConfig = Field(default_factory=VisualTaskConfig)


class KeysConfig(BaseModel):
    same: str = "f"
    different: str = "j"
    secondary_true: str = "f"
    secondary_false: str = "j"
    continue_: str = Field(" ", alias="continue")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _check(self) -> "KeysConfig":
        if self.same == self.different:
            raise ValueError("same and different keys must differ")
        if self.secondary_true == self.secondary_false:
            raise ValueError("secondary true/false keys must differ")
        return self


class AnalysisConfig(BaseModel):
    alpha: float = Field(0.05, gt=0, lt=0.5)
    min_valid_rt_ms: float = Field(200, ge=0, le=1000)
    timing_tolerance_extra_ms: float = Field(5, ge=0, le=100)
    max_memory_stimulus_deviation_frames: float = Field(1, ge=0, le=10)
    max_other_phase_deviation_ms: float = Field(50, ge=0, le=1000)
    min_valid_trials_per_condition: int = Field(15, ge=1)
    max_timeout_rate: float = Field(0.25, ge=0, le=1)
    max_same_key_proportion: float = Field(0.9, gt=0.5, le=1)
    min_secondary_accuracy: float = Field(0.6, ge=0, le=1)
    ies_min_accuracy: float = Field(0.6, ge=0, le=1)
    min_group_size_for_inference: int = Field(5, ge=2)
    normality_alpha: float = Field(0.05, gt=0, lt=0.5)


class ExperimentConfig(BaseModel):
    schema_version: int = 1
    name: str = "SMIT configuration"
    description: str = ""
    grid: GridConfig = Field(default_factory=GridConfig)
    timing: TimingConfig = Field(default_factory=TimingConfig)
    trials: TrialsConfig = Field(default_factory=TrialsConfig)
    secondary_tasks: SecondaryTasksConfig = Field(default_factory=SecondaryTasksConfig)
    keys: KeysConfig = Field(default_factory=KeysConfig)
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)

    @model_validator(mode="after")
    def _check(self) -> "ExperimentConfig":
        n_cells = self.grid.size**2
        needed = 3 * (self.trials.practice_per_condition + self.trials.trials_per_condition)
        available = comb(n_cells, self.grid.highlight_count)
        if needed > available:
            raise ValueError(
                f"Not enough distinct patterns: {needed} trials need unique patterns but only "
                f"{available} exist for {self.grid.highlight_count} of {n_cells} cells"
            )
        if self.secondary_tasks.visual.highlight_count >= n_cells:
            raise ValueError("visual highlight_count must be smaller than the number of cells")
        if self.secondary_tasks.visual.probe == "centre" and self.grid.size % 2 == 0:
            raise ValueError("centre probe requires an odd grid size")
        if self.analysis.min_valid_trials_per_condition > self.trials.trials_per_condition:
            raise ValueError("min_valid_trials_per_condition cannot exceed trials_per_condition")
        return self

    def to_json_dict(self) -> dict:
        return self.model_dump(mode="json", by_alias=True)

    def canonical_hash(self) -> str:
        payload = self.to_json_dict()
        # name/description are labels, not parameters
        payload = {k: v for k, v in payload.items() if k not in ("name", "description")}
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def deviates_from_specification(self) -> list[str]:
        """List differences from the assignment-specified design (warnings, not errors)."""
        notes = []
        t, tr = self.timing, self.trials
        spec = {
            "fixation_ms": 500, "memory_stimulus_ms": 500, "interference_ms": 3000,
            "retention_ms": 1000, "recognition_deadline_ms": 2000, "iti_min_ms": 800, "iti_max_ms": 1200,
        }
        for k, v in spec.items():
            if getattr(t, k) != v:
                notes.append(f"timing.{k} = {getattr(t, k)} (specification: {v})")
        if tr.trials_per_condition != 20:
            notes.append(f"trials.trials_per_condition = {tr.trials_per_condition} (specification: 20)")
        if tr.practice_per_condition != 2:
            notes.append(f"trials.practice_per_condition = {tr.practice_per_condition} (specification: 2)")
        if self.grid.size != 3:
            notes.append(f"grid.size = {self.grid.size} (specification: 3)")
        if self.grid.highlight_count != 4:
            notes.append(f"grid.highlight_count = {self.grid.highlight_count} (specification: 4)")
        if abs(tr.same_proportion - 0.5) > 1e-9:
            notes.append(f"trials.same_proportion = {tr.same_proportion} (specification: 0.5)")
        return notes


def experiment_version_string(version_number: int, config_hash: str) -> str:
    return f"SMIT-v{version_number}-{config_hash[:8]}"
