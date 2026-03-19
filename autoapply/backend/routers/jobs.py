"""Jobs router — list, filter, and trigger scraping."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from middleware.auth import get_current_user_id
from models.orm import Job, User
from models.schemas import JobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _get_user(clerk_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/", response_model=list[JobRead])
async def list_jobs(
    min_score: float = Query(default=0.0, ge=0, le=100),
    status_filter: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[JobRead]:
    """List all scraped jobs with optional filtering."""
    try:
        query = select(Job).where(Job.match_score >= min_score)
        if status_filter:
            query = query.where(Job.status == status_filter)
        query = query.order_by(Job.match_score.desc().nullslast()).limit(limit).offset(offset)
        result = await db.execute(query)
        return [JobRead.model_validate(j) for j in result.scalars().all()]
    except Exception as exc:
        logger.error(f"Error listing jobs: {exc}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: str,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> JobRead:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job)


@router.post("/{job_id}/ignore", status_code=status.HTTP_204_NO_CONTENT)
async def ignore_job(
    job_id: str,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "ignored"
    await db.flush()
