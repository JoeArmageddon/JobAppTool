"""Applications router — create, tailor, status-update, list applications."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.database import get_db
from middleware.auth import get_current_user_id
from models.orm import Application, HuntProfile, Job, Resume, User
from models.schemas import (
    ApplicationCreate,
    ApplicationRead,
    ApplicationStatusUpdate,
    TailorRequest,
)
from services.cover_letter import generate_cover_letter
from services.resume_tailor import tailor_resume

router = APIRouter(prefix="/applications", tags=["applications"])


async def _get_user(clerk_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/tailor", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def tailor_application(
    data: TailorRequest,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationRead:
    """Run AI tailoring for a job+resume pair and create an application record."""
    try:
        user = await _get_user(clerk_id, db)

        # Fetch resume (enforce ownership)
        r_result = await db.execute(
            select(Resume).where(Resume.id == data.resume_id, Resume.user_id == user.id)
        )
        resume = r_result.scalar_one_or_none()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")

        # Fetch job
        j_result = await db.execute(select(Job).where(Job.id == data.job_id))
        job = j_result.scalar_one_or_none()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        jd_text = job.description_raw or ""
        resume_json = resume.structured_json or {}

        logger.info(f"Tailoring resume {resume.id} for job {job.id}")
        tailored_json, _gap = await tailor_resume(resume_json, jd_text)
        cover_letter = await generate_cover_letter(
            tailored_json, job.title, job.company, jd_text
        )

        app = Application(
            user_id=user.id,
            job_id=job.id,
            resume_id=resume.id,
            tailored_resume_text=json.dumps(tailored_json),
            cover_letter_text=cover_letter,
            status="queued",
        )
        db.add(app)
        await db.flush()

        # Eagerly reload with job relationship
        await db.refresh(app)
        return ApplicationRead.model_validate(app)

    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error tailoring application: {exc}")
        raise HTTPException(status_code=500, detail="Failed to tailor application")


@router.get("/", response_model=list[ApplicationRead])
async def list_applications(
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationRead]:
    user = await _get_user(clerk_id, db)
    result = await db.execute(
        select(Application)
        .where(Application.user_id == user.id)
        .options(selectinload(Application.job))
        .order_by(Application.created_at.desc())
    )
    return [ApplicationRead.model_validate(a) for a in result.scalars().all()]


@router.get("/{app_id}", response_model=ApplicationRead)
async def get_application(
    app_id: str,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationRead:
    user = await _get_user(clerk_id, db)
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id, Application.user_id == user.id)
        .options(selectinload(Application.job))
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationRead.model_validate(app)


@router.patch("/{app_id}/status", response_model=ApplicationRead)
async def update_application_status(
    app_id: str,
    data: ApplicationStatusUpdate,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationRead:
    user = await _get_user(clerk_id, db)
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id, Application.user_id == user.id)
        .options(selectinload(Application.job))
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = data.status
    if data.notes:
        app.notes = data.notes
    if data.status == "applied" and not app.applied_at:
        app.applied_at = datetime.now(timezone.utc)
    if data.status in ("interview", "rejected", "offer") and not app.response_at:
        app.response_at = datetime.now(timezone.utc)
    await db.flush()
    return ApplicationRead.model_validate(app)
