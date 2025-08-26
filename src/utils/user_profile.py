from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.level_system import LevelSystem
from typing import Dict
from fastapi import Depends
from src.utils.db import get_db
from src.models.user_profile import UserProfile


def calculate_level_from_xp(total_xp: int, db: Session = Depends(get_db)) -> int:
    """Calculate current level based on XP"""
    levels = db.scalars(select(LevelSystem).order_by(LevelSystem.level.desc())).all()

    for level in levels:
        if total_xp >= level.min_xp_required:
            return level.level

    return 1


def calculate_level_progress(total_xp: int, current_level: int, db: Session = Depends(get_db)) -> Dict:
    """Calculate XP progress within current level"""
    current_level_info = db.scalars(
        select(LevelSystem).where(LevelSystem.level == current_level)
    ).first()

    if not current_level_info:
        return {"xp_progress": 0, "xp_needed_for_next": 0}

    # XP progress in current level
    xp_progress = total_xp - current_level_info.min_xp_required

    # XP needed for next level
    next_level_info = db.scalars(
        select(LevelSystem).where(LevelSystem.level == current_level + 1)
    ).first()

    if next_level_info:
        xp_needed_for_next = next_level_info.min_xp_required - total_xp
    else:
        xp_needed_for_next = 0  # Max level reached

    return {
        "xp_progress": max(0, xp_progress),
        "xp_needed_for_next": max(0, xp_needed_for_next)
    }


def validate_display_name(display_name: str) -> bool:
    """Validate display name format"""
    if len(display_name) < 3 or len(display_name) > 30:
        return False

    # Only allow alphanumeric, spaces, and underscores
    allowed_chars = display_name.replace(" ", "").replace("_", "")
    return allowed_chars.isalnum()


def format_profile_response(profile: UserProfile, db: Session = Depends(get_db)) -> UserProfile:
    """Add calculated fields to profile response"""
    if profile.level_info:
        progress_info = calculate_level_progress(profile.total_xp, profile.current_level, db)
        profile.level_info.xp_progress = progress_info["xp_progress"]
        profile.level_info.xp_needed_for_next = progress_info["xp_needed_for_next"]

    return profile
