from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from src.models.user_profile import UserProfile
from src.models.level_system import LevelSystem
from src.schemas.user_profile import UserProfileUpdate
from typing import Optional
from datetime import datetime, timezone


def create_user_profile(db: Session, user_id: int, display_name: str) -> UserProfile:
    """Create a new user profile"""
    try:
        db_profile = UserProfile(
            user_id=user_id,
            display_name=display_name,
            total_xp=0,
            current_level=1,
            coins=0,
            total_games_played=0
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile
    except IntegrityError:
        db.rollback()
        raise ValueError("Profile already exists for this user")


def get_user_profile(db: Session, user_id: int) -> Optional[UserProfile]:
    """Get user profile with level info"""
    stmt = select(UserProfile).options(selectinload(UserProfile.level_info)).where(UserProfile.user_id == user_id)
    return db.scalars(stmt).first()


def get_user_profile_by_id(db: Session, profile_id: int) -> Optional[UserProfile]:
    """Get profile by profile ID with level info"""
    stmt = select(UserProfile).options(selectinload(UserProfile.level_info)).where(UserProfile.id == profile_id)
    return db.scalars(stmt).first()


def update_user_profile(db: Session, user_id: int, profile_update: UserProfileUpdate) -> Optional[UserProfile]:
    """Update user profile editable fields"""
    try:
        # Check if display name is taken by another user
        if profile_update.display_name:
            existing = db.scalars(
                select(UserProfile).where(
                    UserProfile.display_name == profile_update.display_name,
                    UserProfile.user_id != user_id
                )
            ).first()
            if existing:
                raise ValueError("Display name already taken")

        # Update profile - EXCLUDE user_id from update
        update_data = profile_update.model_dump(exclude_unset=True)
        if update_data:
            update_data['updated_at'] = datetime.now(timezone.utc)
            # IMPORTANT: Remove user_id if present (should never be in update)
            update_data.pop('user_id', None)  # ADD THIS LINE
            
            stmt = update(UserProfile).where(UserProfile.user_id == user_id).values(**update_data)
            result = db.execute(stmt)
            if result.rowcount == 0:
                return None
            db.commit()

        return get_user_profile(db, user_id)
    except IntegrityError:
        db.rollback()
        raise ValueError("Display name already taken")


def update_profile_stats(db: Session, user_id: int, xp_gained: int, coins_gained: int, games_played: int = 1) -> Optional[UserProfile]:
    """Update profile stats after quiz completion"""
    try:
        # Get current profile
        profile = get_user_profile(db, user_id)
        if not profile:
            return None

        # Calculate new values
        new_xp = profile.total_xp + xp_gained
        new_coins = profile.coins + coins_gained
        new_games = profile.total_games_played + games_played

        # Check for level up
        new_level = calculate_level_from_xp(db, new_xp)

        # Update profile
        stmt = update(UserProfile).where(UserProfile.user_id == user_id).values(
            total_xp=new_xp,
            current_level=new_level,
            coins=new_coins,
            total_games_played=new_games,
            updated_at=datetime.now(timezone.utc)
        )
        db.execute(stmt)
        db.commit()

        return get_user_profile(db, user_id)
    except Exception as e:
        db.rollback()
        raise e


def check_display_name_available(db: Session, display_name: str, exclude_user_id: Optional[int] = None) -> bool:
    """Check if display name is available"""
    query = select(UserProfile).where(UserProfile.display_name == display_name)
    if exclude_user_id:
        query = query.where(UserProfile.user_id != exclude_user_id)

    result = db.scalars(query).first()
    return result is None


def get_user_rank(db: Session, user_id: int) -> int:
    """Get user's global rank by XP"""
    profile = get_user_profile(db, user_id)
    if not profile:
        return 0

    # Count users with higher XP
    higher_xp_count = db.scalar(
        select(func.count(UserProfile.id)).where(UserProfile.total_xp > profile.total_xp)
    )

    return higher_xp_count + 1


def calculate_level_from_xp(db: Session, total_xp: int) -> int:
    """Calculate current level based on XP using LevelSystem table"""

    # Get all levels ordered by level desc (highest first)
    levels = db.scalars(
        select(LevelSystem).order_by(LevelSystem.level.desc())
    ).all()

    # Find the highest level the user qualifies for
    for level in levels:
        if total_xp >= level.min_xp_required:
            return level.level

    # If no level found (shouldn't happen), return level 1
    return 1
