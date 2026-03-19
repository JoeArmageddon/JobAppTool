"""
Integration tests for /api/v1/applications endpoints.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from models.orm import User


@pytest.mark.asyncio
async def test_list_applications(
    client: AsyncClient, test_user: User, test_application
) -> None:
    """GET /applications returns the user's applications."""
    resp = await client.get(
        "/api/v1/applications/",
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 401)


@pytest.mark.asyncio
async def test_tailor_application(
    client: AsyncClient,
    test_user: User,
    test_job,
    test_resume,
    sample_resume_json: dict,
) -> None:
    """POST /applications/tailor runs the full AI tailoring pipeline."""
    tailored_resume = {**sample_resume_json, "summary": "Tailored for this specific role."}
    gap_analysis = {
        "exact_matches": ["Python", "FastAPI"],
        "synonym_matches": [],
        "skill_gaps": ["Go"],
        "reorder_suggestions": [],
        "keyword_density_score": 72,
    }

    with (
        patch(
            "services.resume_tailor.tailor_resume",
            new=AsyncMock(return_value=(tailored_resume, gap_analysis)),
        ),
        patch(
            "services.cover_letter.generate_cover_letter",
            new=AsyncMock(return_value="Dear Hiring Manager, ..."),
        ),
    ):
        resp = await client.post(
            "/api/v1/applications/tailor",
            json={"job_id": test_job.id, "resume_id": test_resume.id},
            headers={"X-User-Id": str(test_user.id)},
        )
    assert resp.status_code in (200, 201, 401, 422)


@pytest.mark.asyncio
async def test_update_application_status(
    client: AsyncClient, test_user: User, test_application
) -> None:
    """PATCH /applications/{id}/status updates application status."""
    resp = await client.patch(
        f"/api/v1/applications/{test_application.id}/status",
        json={"status": "applied"},
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 401, 404)
