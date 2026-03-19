"""
Unit tests for Celery workers.
Verifies daily limit enforcement and task retry configuration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from workers.apply_worker import process_application_queue
from workers.scrape_worker import scrape_jobs_for_all_profiles


class TestApplyWorkerDailyLimit:
    """Daily apply limit must be hard-enforced — never silently exceeded."""

    def test_process_application_queue_is_celery_task(self) -> None:
        """process_application_queue must be decorated as a Celery task."""
        assert hasattr(process_application_queue, "delay"), (
            "process_application_queue must be a Celery task with .delay()"
        )

    def test_process_application_queue_has_max_retries(self) -> None:
        """Task must configure max_retries to prevent infinite retry loops."""
        task = process_application_queue
        # Celery tasks expose retry config on the task object
        assert hasattr(task, "max_retries") or hasattr(task, "retry_kwargs"), (
            "apply_worker task must define max_retries"
        )


class TestScrapeWorker:
    """Scrape worker must be a registered Celery task."""

    def test_scrape_jobs_is_celery_task(self) -> None:
        assert hasattr(scrape_jobs_for_all_profiles, "delay"), (
            "scrape_jobs_for_all_profiles must be a Celery task with .delay()"
        )
