"""
Pytest fixtures shared across all integration tests.

Uses an in-memory SQLite database so tests run without Docker.
The AsyncSession and override pattern mirrors production usage exactly.
"""

import asyncio
import json
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Point tests at a test DB before importing anything that reads env
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")
os.environ.setdefault("CLERK_SECRET_KEY", "test-clerk-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:x@localhost/x")

from db.database import Base, get_db  # noqa: E402
from main import app  # noqa: E402
from models.orm import Application, HuntProfile, Job, Resume, User  # noqa: E402

# In-memory SQLite for tests (no Docker required)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession) -> User:
    user = User(clerk_id="test_clerk_id", email="test@example.com")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
def sample_resume_json() -> dict:
    return {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "555-0100",
        "location": "San Francisco, CA",
        "linkedin": "linkedin.com/in/janesmith",
        "github": "github.com/janesmith",
        "summary": "Senior software engineer with 8 years in Python and distributed systems.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
        "experience": [
            {
                "company": "Acme Corp",
                "title": "Senior Software Engineer",
                "start_date": "2020-01",
                "end_date": None,
                "current": True,
                "responsibilities": ["Led migration of monolith to microservices"],
                "achievements": ["Reduced p99 latency by 40%"],
            }
        ],
        "education": [
            {
                "institution": "State University",
                "degree": "B.S. Computer Science",
                "year": 2016,
            }
        ],
        "certifications": [],
        "languages": [],
        "projects": [],
    }


@pytest_asyncio.fixture
async def test_resume(db: AsyncSession, test_user: User, sample_resume_json: dict) -> Resume:
    resume = Resume(
        user_id=test_user.id,
        raw_text="Jane Smith\nSenior Software Engineer\n...",
        structured_json=sample_resume_json,
        ats_score=78,
        impact_score=72,
        completeness_score=85,
        overall_score=78,
        suggestions_json=[],
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@pytest_asyncio.fixture
async def test_hunt_profile(db: AsyncSession, test_user: User) -> HuntProfile:
    profile = HuntProfile(
        user_id=test_user.id,
        target_titles=["Software Engineer", "Backend Engineer"],
        industries=["Technology"],
        locations=["San Francisco, CA", "Remote"],
        remote_preference="remote",
        seniority_level="senior",
        salary_floor=140000,
        company_size_pref="any",
        blacklisted_companies=[],
        job_sources=["linkedin", "indeed"],
        is_active=True,
        daily_apply_limit=10,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@pytest_asyncio.fixture
async def test_job(db: AsyncSession) -> Job:
    job = Job(
        title="Senior Backend Engineer",
        company="TechCo",
        location="San Francisco, CA",
        description_raw="We are looking for a Senior Backend Engineer with Python experience...",
        description_parsed_json={"required_skills": ["Python", "FastAPI"]},
        source="linkedin",
        source_url="https://jobs.greenhouse.io/techco/senior-backend-engineer",
        source_job_id="techco-sbe-001",
        match_score=85,
        match_reasons_json=["Python match", "FastAPI match"],
        status="new",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@pytest_asyncio.fixture
async def test_application(
    db: AsyncSession, test_user: User, test_job: Job, test_resume: Resume
) -> Application:
    application = Application(
        user_id=test_user.id,
        job_id=test_job.id,
        resume_id=test_resume.id,
        tailored_resume_text=json.dumps(
            {
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "555-0100",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
            }
        ),
        cover_letter_text="Dear Hiring Manager,\n\nI am excited to apply...",
        status="queued",
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application
