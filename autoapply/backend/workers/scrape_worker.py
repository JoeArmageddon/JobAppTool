"""
Scrape worker — Celery task that runs every 6 hours.
Fetches active hunt profiles and scrapes matching jobs.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select

from celery_app import app
from db.database import AsyncSessionLocal
from models.orm import HuntProfile, Job, Resume
from services.job_scraper import parse_jd, score_job_match, scrape_jobs_for_profile


@app.task(
    name="workers.scrape_worker.run_job_scrape_for_all_active_profiles",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def run_job_scrape_for_all_active_profiles(self) -> dict:
    """Scrape jobs for all active hunt profiles and match against user resumes."""
    logger.info(f"[scrape_worker] Task started at {datetime.now(timezone.utc)}")
    try:
        result = asyncio.run(_scrape_all_profiles())
        logger.info(f"[scrape_worker] Completed: {result}")
        return result
    except Exception as exc:
        logger.error(f"[scrape_worker] Failed: {exc}")
        raise self.retry(exc=exc)


async def _scrape_all_profiles() -> dict:
    total_new = 0
    total_skipped = 0

    async with AsyncSessionLocal() as db:
        # Get all active hunt profiles
        profiles_result = await db.execute(
            select(HuntProfile).where(HuntProfile.is_active == True)
        )
        profiles = profiles_result.scalars().all()
        logger.info(f"[scrape_worker] Processing {len(profiles)} active profiles")

        for profile in profiles:
            # Get the latest resume for this user
            resume_result = await db.execute(
                select(Resume)
                .where(Resume.user_id == profile.user_id)
                .order_by(Resume.created_at.desc())
                .limit(1)
            )
            resume = resume_result.scalar_one_or_none()
            if not resume or not resume.structured_json:
                logger.warning(f"[scrape_worker] User {profile.user_id} has no parsed resume, skipping")
                continue

            raw_jobs = scrape_jobs_for_profile(
                target_titles=profile.target_titles or [],
                locations=profile.locations or [],
                job_sources=profile.job_sources or ["linkedin", "indeed"],
            )

            for raw_job in raw_jobs:
                source_job_id = str(raw_job.get("source_job_id", ""))

                # Check deduplication
                existing = await db.execute(
                    select(Job).where(Job.source_job_id == source_job_id)
                )
                if existing.scalar_one_or_none():
                    total_skipped += 1
                    continue

                # Parse JD
                description = str(raw_job.get("description", ""))
                try:
                    jd_parsed = await parse_jd(description)
                except Exception as exc:
                    logger.warning(f"[scrape_worker] JD parse failed for {source_job_id}: {exc}")
                    jd_parsed = {}

                # Score match
                try:
                    match_result = await score_job_match(resume.structured_json, jd_parsed)
                    match_score = match_result.get("match_score", 0)
                    match_reasons = match_result
                except Exception as exc:
                    logger.warning(f"[scrape_worker] Match scoring failed: {exc}")
                    match_score = 0
                    match_reasons = {}

                # Persist job
                job = Job(
                    id=str(uuid.uuid4()),
                    title=str(raw_job.get("title", "Unknown")),
                    company=str(raw_job.get("company", "Unknown")),
                    location=str(raw_job.get("location", "")),
                    description_raw=description,
                    description_parsed_json=jd_parsed,
                    source=str(raw_job.get("site", "")),
                    source_url=str(raw_job.get("job_url", "")),
                    source_job_id=source_job_id,
                    match_score=match_score,
                    match_reasons_json=match_reasons,
                    status="new",
                )
                db.add(job)
                total_new += 1

        await db.commit()

    return {"new_jobs": total_new, "skipped_duplicates": total_skipped}
