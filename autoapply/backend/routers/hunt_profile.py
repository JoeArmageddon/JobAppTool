"""Hunt profile router — CRUD for job search preferences."""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from middleware.auth import get_current_user_id
from models.orm import HuntProfile, User
from models.schemas import HuntProfileCreate, HuntProfileRead, HuntProfileUpdate

router = APIRouter(prefix="/hunt-profiles", tags=["hunt-profiles"])


async def _get_user(clerk_id: str, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/", response_model=HuntProfileRead, status_code=status.HTTP_201_CREATED)
async def create_hunt_profile(
    data: HuntProfileCreate,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> HuntProfileRead:
    try:
        user = await _get_user(clerk_id, db)
        profile = HuntProfile(user_id=user.id, **data.model_dump())
        db.add(profile)
        await db.flush()
        logger.info(f"Hunt profile created for user {user.id}")
        return HuntProfileRead.model_validate(profile)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error creating hunt profile: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create hunt profile")


@router.get("/", response_model=list[HuntProfileRead])
async def list_hunt_profiles(
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[HuntProfileRead]:
    user = await _get_user(clerk_id, db)
    result = await db.execute(
        select(HuntProfile).where(HuntProfile.user_id == user.id)
    )
    return [HuntProfileRead.model_validate(p) for p in result.scalars().all()]


@router.get("/{profile_id}", response_model=HuntProfileRead)
async def get_hunt_profile(
    profile_id: str,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> HuntProfileRead:
    user = await _get_user(clerk_id, db)
    result = await db.execute(
        select(HuntProfile).where(HuntProfile.id == profile_id, HuntProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Hunt profile not found")
    return HuntProfileRead.model_validate(profile)


@router.put("/{profile_id}", response_model=HuntProfileRead)
async def update_hunt_profile(
    profile_id: str,
    data: HuntProfileUpdate,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> HuntProfileRead:
    user = await _get_user(clerk_id, db)
    result = await db.execute(
        select(HuntProfile).where(HuntProfile.id == profile_id, HuntProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Hunt profile not found")
    for key, value in data.model_dump().items():
        setattr(profile, key, value)
    await db.flush()
    return HuntProfileRead.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hunt_profile(
    profile_id: str,
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    user = await _get_user(clerk_id, db)
    result = await db.execute(
        select(HuntProfile).where(HuntProfile.id == profile_id, HuntProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Hunt profile not found")
    await db.delete(profile)
