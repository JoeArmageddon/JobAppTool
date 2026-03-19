"""Resume router — upload, parse, score, and retrieve resumes."""

import os
import uuid
from pathlib import Path
from typing import Annotated

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from middleware.auth import get_current_user_id
from models.orm import Resume, User
from models.schemas import ResumeRead
from services.resume_parser import extract_text, parse_resume
from services.resume_scorer import score_resume

router = APIRouter(prefix="/resumes", tags=["resumes"])

ALLOWED_TYPES = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", "/app/uploads"))


async def _get_or_create_user(clerk_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(clerk_id=clerk_id, email=f"{clerk_id}@placeholder.autoapply")
        db.add(user)
        await db.flush()
    return user


@router.post("/upload", response_model=ResumeRead, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: Annotated[UploadFile, File(description="PDF or DOCX resume")],
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ResumeRead:
    """Upload a resume, parse it with Claude, score it, and persist to DB."""
    try:
        # Validate MIME type
        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unsupported file type: {file.content_type}. Upload PDF or DOCX.",
            )

        # Read and validate size
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File exceeds 10 MB limit.",
            )

        # Save file to disk (user-scoped path — no predictable URLs)
        user = await _get_or_create_user(clerk_id, db)
        file_id = str(uuid.uuid4())
        ext = ".pdf" if "pdf" in file.content_type else ".docx"
        user_dir = UPLOADS_DIR / user.id
        user_dir.mkdir(parents=True, exist_ok=True)
        file_path = user_dir / f"{file_id}{ext}"

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_bytes)

        # Parse and score
        logger.info(f"Parsing resume for user {user.id}")
        raw_text = extract_text(file_bytes, file.content_type)
        structured = await parse_resume(raw_text)
        scores = await score_resume(structured)

        # Persist
        resume = Resume(
            user_id=user.id,
            raw_text=raw_text,
            structured_json=structured,
            ats_score=scores["ats_score"],
            impact_score=scores["impact_score"],
            completeness_score=scores["completeness_score"],
            overall_score=scores["overall_score"],
            suggestions_json=scores.get("suggestions", []),
            file_url=str(file_path),
            original_filename=file.filename,
        )
        db.add(resume)
        await db.flush()

        logger.info(f"Resume {resume.id} processed for user {user.id} — score {scores['overall_score']:.1f}")
        return ResumeRead.model_validate(resume)

    except HTTPException:
        raise
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error in resume upload: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.get("/", response_model=list[ResumeRead])
async def list_resumes(
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[ResumeRead]:
    user = await _get_or_create_user(clerk_id, db)
    result = await db.execute(
        select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
    )
    resumes = result.scalars().all()
    return [ResumeRead.model_validate(r) for r in resumes]


@router.get("/{resume_id}", response_model=ResumeRead)
async def get_resume(
    resume_id: str,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ResumeRead:
    user = await _get_or_create_user(clerk_id, db)
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return ResumeRead.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: str,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    user = await _get_or_create_user(clerk_id, db)
    result = await db.execute(
        select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    # Remove stored file
    if resume.file_url:
        Path(resume.file_url).unlink(missing_ok=True)
    await db.delete(resume)
