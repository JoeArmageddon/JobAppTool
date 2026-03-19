"""
Apply worker — processes queued applications, enforces daily limit.
Never exceeds the user's daily_apply_limit.
"""

import asyncio
from datetime import datetime, date, timezone

from loguru import logger
from sqlalchemy import func, select

from celery_app import app
from db.database import AsyncSessionLocal
from models.orm import Application, HuntProfile, User
from services.apply_engine import apply_to_job


@app.task(
    name="workers.apply_worker.process_application_queue",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_application_queue(self, user_id: str) -> dict:
    """Process queued applications for a user, respecting the daily limit."""
    logger.info(f"[apply_worker] Processing queue for user {user_id}")
    try:
        result = asyncio.run(_process_queue(user_id))
        logger.info(f"[apply_worker] Done for {user_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"[apply_worker] Failed for {user_id}: {exc}")
        raise self.retry(exc=exc)


async def _process_queue(user_id: str) -> dict:
    applied = 0
    failed = 0
    requires_human = 0
    limit_hit = False

    async with AsyncSessionLocal() as db:
        # Get user's active hunt profile for daily limit
        profile_result = await db.execute(
            select(HuntProfile)
            .where(HuntProfile.user_id == user_id, HuntProfile.is_active == True)
            .limit(1)
        )
        profile = profile_result.scalar_one_or_none()
        daily_limit = profile.daily_apply_limit if profile else 10

        # Count applications already sent today
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
        today_count_result = await db.execute(
            select(func.count(Application.id)).where(
                Application.user_id == user_id,
                Application.status == "applied",
                Application.applied_at >= today_start,
            )
        )
        today_count = today_count_result.scalar() or 0

        remaining = daily_limit - today_count
        if remaining <= 0:
            logger.info(f"[apply_worker] Daily limit ({daily_limit}) reached for user {user_id}")
            return {"applied": 0, "failed": 0, "requires_human": 0, "limit_hit": True}

        # Fetch queued applications
        queued_result = await db.execute(
            select(Application)
            .where(Application.user_id == user_id, Application.status == "queued")
            .limit(remaining)
        )
        queued = queued_result.scalars().all()

        for application in queued:
            if applied >= remaining:
                limit_hit = True
                break

            logger.info(f"[apply_worker] Applying for application {application.id}")
            application.status = "applying"
            await db.flush()

            try:
                outcome = await apply_to_job(application)
                if outcome == "success":
                    application.status = "applied"
                    application.applied_at = datetime.now(timezone.utc)
                    applied += 1
                elif outcome == "requires_human":
                    application.status = "queued"
                    application.notes = (application.notes or "") + "\n[auto-apply: requires human review]"
                    requires_human += 1
                else:
                    application.status = "queued"
                    failed += 1
            except Exception as exc:
                logger.error(f"[apply_worker] Error applying {application.id}: {exc}")
                application.status = "queued"
                failed += 1

            await db.flush()

        await db.commit()

    if limit_hit:
        logger.info(f"[apply_worker] Daily limit hit for user {user_id}, stopping queue")

    return {
        "applied": applied,
        "failed": failed,
        "requires_human": requires_human,
        "limit_hit": limit_hit,
    }
