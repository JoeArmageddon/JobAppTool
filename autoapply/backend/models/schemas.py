"""Pydantic v2 request/response schemas — mirrors ORM models."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator


# ─── User ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    clerk_id: str
    email: EmailStr


class UserRead(BaseModel):
    id: str
    clerk_id: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Resume ──────────────────────────────────────────────────────────────────

class ResumeSuggestion(BaseModel):
    category: str
    issue: str
    fix: str


class ResumeScores(BaseModel):
    ats_score: float
    impact_score: float
    completeness_score: float
    overall_score: float
    suggestions: list[ResumeSuggestion]


class ResumeRead(BaseModel):
    id: str
    user_id: str
    raw_text: Optional[str] = None
    structured_json: Optional[dict[str, Any]] = None
    ats_score: Optional[float] = None
    impact_score: Optional[float] = None
    completeness_score: Optional[float] = None
    overall_score: Optional[float] = None
    suggestions_json: Optional[list[dict[str, Any]]] = None
    file_url: Optional[str] = None
    original_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Hunt Profile ────────────────────────────────────────────────────────────

class HuntProfileCreate(BaseModel):
    target_titles: list[str] = []
    industries: list[str] = []
    locations: list[str] = []
    remote_preference: str = "hybrid"
    seniority_level: Optional[str] = None
    salary_floor: Optional[int] = None
    company_size_pref: Optional[str] = None
    blacklisted_companies: list[str] = []
    job_sources: list[str] = ["linkedin", "indeed"]
    daily_apply_limit: int = 10
    auto_apply: bool = False

    @field_validator("daily_apply_limit")
    @classmethod
    def clamp_limit(cls, v: int) -> int:
        return max(1, min(50, v))

    @field_validator("remote_preference")
    @classmethod
    def validate_remote(cls, v: str) -> str:
        allowed = {"remote", "hybrid", "onsite"}
        if v not in allowed:
            raise ValueError(f"remote_preference must be one of {allowed}")
        return v


class HuntProfileUpdate(HuntProfileCreate):
    pass


class HuntProfileRead(BaseModel):
    id: str
    user_id: str
    target_titles: list[str]
    industries: list[str]
    locations: list[str]
    remote_preference: str
    seniority_level: Optional[str] = None
    salary_floor: Optional[int] = None
    company_size_pref: Optional[str] = None
    blacklisted_companies: list[str]
    job_sources: list[str]
    is_active: bool
    daily_apply_limit: int
    auto_apply: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Job ─────────────────────────────────────────────────────────────────────

class JobRead(BaseModel):
    id: str
    title: str
    company: str
    location: Optional[str] = None
    description_raw: Optional[str] = None
    description_parsed_json: Optional[dict[str, Any]] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    posted_at: Optional[datetime] = None
    scraped_at: datetime
    match_score: Optional[float] = None
    match_reasons_json: Optional[dict[str, Any]] = None
    status: str

    model_config = {"from_attributes": True}


# ─── Application ─────────────────────────────────────────────────────────────

class ApplicationCreate(BaseModel):
    job_id: str
    resume_id: str


class ApplicationStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"queued", "applying", "applied", "viewed", "interview", "rejected", "offer"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ApplicationRead(BaseModel):
    id: str
    user_id: str
    job_id: str
    resume_id: Optional[str] = None
    tailored_resume_text: Optional[str] = None
    tailored_resume_pdf_url: Optional[str] = None
    cover_letter_text: Optional[str] = None
    status: str
    applied_at: Optional[datetime] = None
    response_at: Optional[datetime] = None
    notes: Optional[str] = None
    screenshot_url: Optional[str] = None
    created_at: datetime
    job: Optional[JobRead] = None

    model_config = {"from_attributes": True}


# ─── API wrappers ────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    code: str


class TailorRequest(BaseModel):
    job_id: str
    resume_id: str
