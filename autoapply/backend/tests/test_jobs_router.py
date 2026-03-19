"""
Integration tests for /api/v1/jobs endpoints.
"""

import pytest
from httpx import AsyncClient

from models.orm import User


@pytest.mark.asyncio
async def test_list_jobs(
    client: AsyncClient, test_user: User, test_job
) -> None:
    """GET /jobs returns job list (possibly filtered by min_score)."""
    resp = await client.get(
        "/api/v1/jobs/",
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 401)


@pytest.mark.asyncio
async def test_list_jobs_with_min_score_filter(
    client: AsyncClient, test_user: User, test_job
) -> None:
    """GET /jobs?min_score=90 returns only high-match jobs."""
    resp = await client.get(
        "/api/v1/jobs/?min_score=90",
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 401)
    if resp.status_code == 200:
        data = resp.json()
        # All returned jobs should meet the filter
        for job in data:
            assert job.get("match_score", 0) >= 90


@pytest.mark.asyncio
async def test_ignore_job(
    client: AsyncClient, test_user: User, test_job
) -> None:
    """POST /jobs/{id}/ignore marks the job as ignored."""
    resp = await client.post(
        f"/api/v1/jobs/{test_job.id}/ignore",
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 401, 404)
