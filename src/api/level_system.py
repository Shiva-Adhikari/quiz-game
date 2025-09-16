# === Standard library imports ===
from typing import List

# === Third-party imports ===
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, status, Query, Depends

# === Local imports ===
from src.utils.db import get_db
from src.models.level_system import LevelSystem
from src.schemas.level_system import (
    BulkLevelCreate,
    LevelSystemCreate,
    LevelSystemUpdate,
    LevelSystemResponse
)
from src.crud.level_system import (
    _create_level,
    _update_level,
    _delete_level,
    _get_level_by_xp,
    _get_level_by_number,
    _get_levels_paginated,
)


router = APIRouter(prefix="/levels", tags=["level_system"])


@router.get("/", response_model=List[LevelSystemResponse])
def get_all_levels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all levels with pagination"""
    levels = _get_levels_paginated(db, skip=skip, limit=limit)
    return levels


@router.get("/{level_number}", response_model=LevelSystemResponse)
def get_level(level_number: int, db: Session = Depends(get_db)):
    """Get specific level by number"""
    if level_number < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Level number must be positive"
        )

    level = _get_level_by_number(db, level_number)
    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Level not found"
        )

    return level


@router.get("/xp/{xp_amount}", response_model=LevelSystemResponse)
def get_level_by_xp(xp_amount: int, db: Session = Depends(get_db)):
    """Get level based on XP amount"""
    if xp_amount < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="XP amount cannot be negative"
        )

    level = _get_level_by_xp(db, xp_amount)
    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No level found for this XP amount"
        )

    return level


@router.put("/{level_number}", response_model=LevelSystemResponse)
def update_level(
    level_number: int,
    level_update: LevelSystemUpdate,
    db: Session = Depends(get_db),
    # current_admin = Depends(get_current_admin_user)  # Add if you have admin auth
):
    """Update level (Admin only)"""
    level = _update_level(db, level_number, level_update)
    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Level not found"
        )

    return level


@router.delete("/{level_number}")
def delete_level(
    level_number: int,
    db: Session = Depends(get_db),
    # current_admin = Depends(get_current_admin_user)  # Add if you have admin auth
):
    """Delete level (Admin only)"""
    success = _delete_level(db, level_number)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Level not found"
        )

    return {"message": "Level deleted successfully"}


@router.post("/", response_model=LevelSystemResponse)
def create_level(level_data: LevelSystemCreate, db: Session = Depends(get_db)):
    """Create new level (Admin only)"""

    # Validate level number
    if level_data.level < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Level must be positive"
        )

    # Validate XP ranges
    if level_data.min_xp_required < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum XP cannot be negative"
        )

    if level_data.max_xp_required <= level_data.min_xp_required:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum XP must be greater than minimum XP"
        )

    # Check for existing level
    existing = _get_level_by_number(db, level_data.level)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Level {level_data.level} already exists"
        )

    # Check for overlapping XP ranges
    overlapping = db.query(LevelSystem).filter(
        ((LevelSystem.min_xp_required <= level_data.min_xp_required) & 
         (LevelSystem.max_xp_required >= level_data.min_xp_required)) |
        ((LevelSystem.min_xp_required <= level_data.max_xp_required) & 
         (LevelSystem.max_xp_required >= level_data.max_xp_required))
    ).first()

    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"XP range overlaps with level {overlapping.level}"
        )

    try:
        level = _create_level(db, level_data)
        return level
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create level: {str(e)}"
        )


# Add this to your level_system router
@router.post("/bulk", response_model=List[LevelSystemResponse])
def create_levels_bulk(
    bulk_data: BulkLevelCreate,
    db: Session = Depends(get_db)
):
    """Create multiple levels at once (Admin only)"""

    if not bulk_data.levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No levels provided"
        )

    # Validate all levels before creating any
    level_numbers = set()
    xp_ranges = []

    for level_data in bulk_data.levels:
        # Validate level number
        if level_data.level < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Level {level_data.level} must be positive"
            )

        # Check for duplicates in the batch
        if level_data.level in level_numbers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Duplicate level {level_data.level} in batch"
            )
        level_numbers.add(level_data.level)

        # Validate XP ranges
        if level_data.min_xp_required < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Level {level_data.level}: Minimum XP cannot be negative"
            )

        if level_data.max_xp_required <= level_data.min_xp_required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Level {level_data.level}: Maximum XP must be greater than minimum XP"
            )

        xp_ranges.append({
            'level': level_data.level,
            'min_xp': level_data.min_xp_required,
            'max_xp': level_data.max_xp_required
        })

    # Check for existing levels in database
    existing_levels = db.query(LevelSystem).filter(
        LevelSystem.level.in_(level_numbers)
    ).all()

    if existing_levels:
        existing_numbers = [level.level for level in existing_levels]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Levels already exist: {existing_numbers}"
        )

    # Check for overlapping XP ranges within the batch
    sorted_ranges = sorted(xp_ranges, key=lambda x: x['min_xp'])
    for i in range(len(sorted_ranges) - 1):
        current = sorted_ranges[i]
        next_range = sorted_ranges[i + 1]

        if current['max_xp'] > next_range['min_xp']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"XP ranges overlap between levels {current['level']} and {next_range['level']}"
            )

    # Check for overlapping with existing database ranges
    for range_data in xp_ranges:
        overlapping = db.query(LevelSystem).filter(
            ((LevelSystem.min_xp_required <= range_data['min_xp']) & 
             (LevelSystem.max_xp_required >= range_data['min_xp'])) |
            ((LevelSystem.min_xp_required <= range_data['max_xp']) & 
             (LevelSystem.max_xp_required >= range_data['max_xp']))
        ).first()

        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Level {range_data['level']} XP range overlaps with existing level {overlapping.level}"
            )

    # Create all levels in a transaction
    try:
        created_levels = []

        for level_data in bulk_data.levels:
            db_level = LevelSystem(**level_data.model_dump())
            db.add(db_level)
            created_levels.append(db_level)

        db.commit()

        # Refresh all objects to get IDs
        for level in created_levels:
            db.refresh(level)

        return created_levels

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create levels: {str(e)}"
        )


# Also add a convenience endpoint to initialize default levels
@router.post("/initialize", response_model=dict)
def initialize_default_levels(db: Session = Depends(get_db)):
    """Initialize the level system with predefined levels"""

    # Check if levels already exist
    existing = db.query(LevelSystem).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Levels already exist. Use DELETE /levels/all to reset first."
        )

    # Default levels from your initialization function
    default_levels = [
        {"level": 1, "level_name": "Beginner", "min_xp_required": 0, "max_xp_required": 99, "description": "Starting your quiz journey"},
        {"level": 2, "level_name": "Novice", "min_xp_required": 100, "max_xp_required": 249, "description": "Learning the basics"},
        {"level": 3, "level_name": "Apprentice", "min_xp_required": 250, "max_xp_required": 499, "description": "Building knowledge"},
        {"level": 4, "level_name": "Student", "min_xp_required": 500, "max_xp_required": 799, "description": "Developing skills"},
        {"level": 5, "level_name": "Scholar", "min_xp_required": 800, "max_xp_required": 1199, "description": "Gaining expertise"},
        {"level": 6, "level_name": "Expert", "min_xp_required": 1200, "max_xp_required": 1699, "description": "Demonstrating mastery"},
        {"level": 7, "level_name": "Master", "min_xp_required": 1700, "max_xp_required": 2299, "description": "Achieving excellence"},
        {"level": 8, "level_name": "Grandmaster", "min_xp_required": 2300, "max_xp_required": 2999, "description": "Reaching new heights"},
        {"level": 9, "level_name": "Champion", "min_xp_required": 3000, "max_xp_required": 3999, "description": "Standing among the best"},
        {"level": 10, "level_name": "Legend", "min_xp_required": 4000, "max_xp_required": 5499, "description": "Legendary status achieved"},
        {"level": 11, "level_name": "Elite", "min_xp_required": 5500, "max_xp_required": 7499, "description": "Elite performer"},
        {"level": 12, "level_name": "Supreme", "min_xp_required": 7500, "max_xp_required": 9999, "description": "Supreme knowledge"},
        {"level": 13, "level_name": "Ultimate", "min_xp_required": 10000, "max_xp_required": 14999, "description": "Ultimate achievement"},
        {"level": 14, "level_name": "Transcendent", "min_xp_required": 15000, "max_xp_required": 24999, "description": "Transcending limits"},
        {"level": 15, "level_name": "Omniscient", "min_xp_required": 25000, "max_xp_required": 999999999, "description": "All-knowing quiz master"}
    ]

    try:
        created_levels = []
        for level_data in default_levels:
            db_level = LevelSystem(**level_data)
            db.add(db_level)
            created_levels.append(db_level)

        db.commit()

        return {
            "message": f"Successfully initialized {len(default_levels)} levels",
            "levels_created": len(created_levels)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize levels: {str(e)}"
        )


# Optional: Add endpoint to clear all levels
@router.delete("/all")
def delete_all_levels(db: Session = Depends(get_db)):
    """Delete all levels (Admin only) - Use with caution!"""
    try:
        count = db.query(LevelSystem).count()
        db.query(LevelSystem).delete()
        db.commit()

        return {
            "message": f"Successfully deleted {count} levels"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete levels: {str(e)}"
        )
