"""Pydantic request/response schemas for the HTTP API."""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

GENDERS = ("Female", "Male", "Non-binary", "Other", "Prefer not to answer")
EMAIL_RE = re.compile(r"^[^@\s<>\"']{1,64}@[A-Za-z0-9.-]{1,180}\.[A-Za-z]{2,24}$")
SAFE_TEXT_RE = re.compile(r"^[^<>{}\\=@+\-\t\r][^<>{}\\]*$")  # leading = + - @ blocked (spreadsheet formula injection)


def clean_text(v: str | None, field: str, max_len: int = 120) -> str | None:
    if v is None:
        return None
    v = " ".join(str(v).split())
    if not v:
        return None
    if len(v) > max_len:
        raise ValueError(f"{field} is too long (max {max_len} characters)")
    if not SAFE_TEXT_RE.match(v):
        raise ValueError(f"{field} contains characters that are not allowed")
    return v


class DeviceInfo(BaseModel):
    user_agent: str | None = Field(None, max_length=500)
    platform: str | None = Field(None, max_length=100)
    language: str | None = Field(None, max_length=40)
    screen_width: int | None = None
    screen_height: int | None = None
    device_pixel_ratio: float | None = None
    viewport_width: int | None = None
    viewport_height: int | None = None
    hardware_concurrency: int | None = None
    estimated_refresh_rate: float | None = None
    touch_capable: bool | None = None


class RegistrationIn(BaseModel):
    consent: bool
    age: int | None = None
    gender: str | None = None
    academic_course: str | None = None
    email: str | None = None
    session_type: Literal["main", "pilot"] = "main"
    pilot_token: str | None = None
    device: DeviceInfo = Field(default_factory=DeviceInfo)

    @field_validator("gender")
    @classmethod
    def _gender(cls, v):
        if v is None:
            return v
        if v not in GENDERS:
            raise ValueError(f"gender must be one of: {', '.join(GENDERS)}")
        return v

    @field_validator("academic_course")
    @classmethod
    def _course(cls, v):
        return clean_text(v, "academic course")

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not EMAIL_RE.match(v):
            raise ValueError("please enter a valid email address")
        return v


class TrialIn(BaseModel):
    trial_number: int = Field(ge=1)
    practice_trial: bool
    practice_attempt: int = Field(0, ge=0, le=10)
    participant_response: Literal["same", "different"] | None = None
    reaction_time_ms: float | None = None
    response_timeout: bool = False
    premature_keypresses: int = Field(0, ge=0, le=1000)
    interference_response: Literal["true", "false"] | None = None
    interference_reaction_time_ms: float | None = None
    actual_fixation_duration_ms: float | None = None
    measured_stimulus_duration_ms: float | None = None
    measured_post_stimulus_blank_ms: float | None = None
    measured_interference_duration_ms: float | None = None
    measured_retention_duration_ms: float | None = None
    inter_trial_interval_ms: float | None = None
    refresh_rate_hz: float | None = None
    dropped_frames: int | None = Field(None, ge=0)
    focus_loss: bool = False
    event_timestamps: dict | None = None


class TrialBatchIn(BaseModel):
    trials: list[TrialIn] = Field(max_length=100)


class SessionEventIn(BaseModel):
    event: Literal["practice_started", "practice_repeated", "main_started", "block_started", "interrupted",
                   "resumed", "fullscreen_exit", "withdrawn"]
    detail: str | None = Field(None, max_length=500)


class StatusChangeIn(BaseModel):
    status: Literal["active", "withdrawn", "excluded"]
    reason: str = Field(min_length=3, max_length=2000)


class DeleteIn(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
    confirm_participant_id: str


class TrialExclusionIn(BaseModel):
    excluded: bool
    reason: str = Field(min_length=3, max_length=2000)


class SessionStatusIn(BaseModel):
    completion_status: Literal["abandoned", "incomplete", "completed"]
    reason: str = Field(min_length=3, max_length=2000)


class ConfigIn(BaseModel):
    config: dict
    notes: str | None = Field(None, max_length=2000)
    parent_id: int | None = None


class ConfigDeleteIn(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
    confirm_version: str = Field(max_length=64)


class LockIn(BaseModel):
    justification: str = Field(min_length=10, max_length=4000)


class LoginIn(BaseModel):
    password: str = Field(max_length=200)


class PilotLaunchIn(BaseModel):
    config_id: int | None = None
