# === Standard library imports ===
from typing import Optional, List

# === Third-party imports ===
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

# === Local imports ===
from src.models.level_system import LevelSystem
from src.schemas.level_system import LevelSystemCreate, LevelSystemUpdate


def _create_level(db: Session, level_data: LevelSystemCreate) -> LevelSystem:
    """Create a new level"""
    db_level = LevelSystem(**level_data.model_dump())
    db.add(db_level)
    db.commit()
    db.refresh(db_level)
    return db_level


def _get_level_by_number(db: Session, level: int) -> Optional[LevelSystem]:
    """Get level by level number"""
    return db.scalars(select(LevelSystem).where(LevelSystem.level == level)).first()


def _get_level_by_xp(db: Session, xp: int) -> Optional[LevelSystem]:
    """Get level based on XP amount"""
    return db.scalars(
        select(LevelSystem)
        .where(LevelSystem.min_xp_required <= xp)
        .order_by(LevelSystem.level.desc())
    ).first()


def _get_all_levels(db: Session) -> List[LevelSystem]:
    """Get all levels ordered by level number"""
    return db.scalars(select(LevelSystem).order_by(LevelSystem.level)).all()


def _get_levels_paginated(db: Session, skip: int = 0, limit: int = 100) -> List[LevelSystem]:
    """Get levels with pagination"""
    return db.scalars(
        select(LevelSystem)
        .order_by(LevelSystem.level)
        .offset(skip)
        .limit(limit)
    ).all()


def _update_level(db: Session, level: int, level_update: LevelSystemUpdate) -> Optional[LevelSystem]:
    """Update level information"""
    update_data = level_update.model_dump(exclude_unset=True)
    if not update_data:
        return _get_level_by_number(db, level)

    stmt = update(LevelSystem).where(LevelSystem.level == level).values(**update_data)
    result = db.execute(stmt)

    if result.rowcount == 0:
        return None

    db.commit()
    return _get_level_by_number(db, level)


def _delete_level(db: Session, level: int) -> bool:
    """Delete a level"""
    stmt = delete(LevelSystem).where(LevelSystem.level == level)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0
