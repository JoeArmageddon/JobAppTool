"""SQLAlchemy ORM models — one class per DB table."""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, ARRAY, JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.database import Base


def _uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    clerk_id = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    hunt_profiles = relationship("HuntProfile", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    raw_text = Column(Text)
    structured_json = Column(JSON)
    ats_score = Column(Float)
    impact_score = Column(Float)
    completeness_score = Column(Float)
    overall_score = Column(Float)
    suggestions_json = Column(JSON)
    file_url = Column(String)
    original_filename = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")


class HuntProfile(Base):
    __tablename__ = "hunt_profiles"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_titles = Column(ARRAY(String), default=list)
    industries = Column(ARRAY(String), default=list)
    locations = Column(ARRAY(String), default=list)
    remote_preference = Column(String, default="hybrid")  # remote | hybrid | onsite
    seniority_level = Column(String)
    salary_floor = Column(Integer)
    company_size_pref = Column(String)
    blacklisted_companies = Column(ARRAY(String), default=list)
    job_sources = Column(ARRAY(String), default=list)
    is_active = Column(Boolean, default=True)
    daily_apply_limit = Column(Integer, default=10)
    auto_apply = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="hunt_profiles")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String)
    description_raw = Column(Text)
    description_parsed_json = Column(JSON)
    source = Column(String)
    source_url = Column(String)
    source_job_id = Column(String, unique=True, index=True)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    posted_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    match_score = Column(Float)
    match_reasons_json = Column(JSON)
    status = Column(String, default="new")  # new | matched | ignored | applied

    applications = relationship("Application", back_populates="job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    resume_id = Column(UUID(as_uuid=False), ForeignKey("resumes.id"), nullable=True)
    tailored_resume_text = Column(Text)
    tailored_resume_pdf_url = Column(String)
    cover_letter_text = Column(Text)
    status = Column(String, default="queued")
    # queued → applying → applied → viewed → interview → rejected | offer
    applied_at = Column(DateTime(timezone=True))
    response_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    screenshot_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")
