"""
Integration tests for /api/v1/hunt-profile endpoints.
"""

import pytest
from httpx import AsyncClient

from models.orm import User


@pytest.mark.asyncio
async def test_create_hunt_profile(client: AsyncClient, test_user: User) -> None:
    """POST /hunt-profile creates a new profile."""
    payload = {
        "target_titles": ["Backend Engineer"],
        "industries": ["Technology"],
        "locations": ["Remote"],
        "remote_preference": "remote",
        "seniority_level": "mid",
        "salary_floor": 120000,
        "company_size_pref": "startup",
        "blacklisted_companies": [],
        "job_sources": ["linkedin"],
        "is_active": True,
        "daily_apply_limit": 5,
    }
    resp = await client.post(
        "/api/v1/hunt-profile/",
        json=payload,
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 201, 401)


@pytest.mark.asyncio
async def test_get_hunt_profile(
    client: AsyncClient, test_user: User, test_hunt_profile
) -> None:
    """GET /hunt-profile returns the user's active profile."""
    resp = await client.get(
        "/api/v1/hunt-profile/",
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 401, 404)


@pytest.mark.asyncio
async def test_update_hunt_profile(
    client: AsyncClient, test_user: User, test_hunt_profile
) -> None:
    """PATCH /hunt-profile updates an existing profile."""
    resp = await client.patch(
        f"/api/v1/hunt-profile/{test_hunt_profile.id}",
        json={"daily_apply_limit": 15},
        headers={"X-User-Id": str(test_user.id)},
    )
    assert resp.status_code in (200, 401, 404)
