from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from typing import List
from src.schemas.level_system import LevelSystemResponse, LevelSystemCreate, LevelSystemUpdate
from src.crud import level_system as crud_level
# Using your existing dependencies: get_db, get_current_admin_user (if you have admin)
from src.utils.db import get_db
from src.models.level_system import LevelSystem


router = APIRouter(prefix="/levels", tags=["level_system"])


@router.get("/", response_model=List[LevelSystemResponse])
def get_all_levels(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all levels with pagination"""
    levels = crud_level.get_levels_paginated(db, skip=skip, limit=limit)
    return levels


@router.get("/{level_number}", response_model=LevelSystemResponse)
def get_level(level_number: int, db: Session = Depends(get_db)):
    """Get specific level by number"""
    if level_number < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Level number must be positive"
        )

    level = crud_level.get_level_by_number(db, level_number)
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

    level = crud_level.get_level_by_xp(db, xp_amount)
    if not level:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No level found for this XP amount"
        )

    return level


'''
# Admin routes (if you have admin functionality)
@router.post("/", response_model=LevelSystemResponse)
def create_level(
    level_data: LevelSystemCreate,
    db: Session = Depends(get_db),
    # current_admin = Depends(get_current_admin_user)  # Add if you have admin auth
):
    """Create new level (Admin only)"""
    try:
        # Check if level already exists
        existing = crud_level.get_level_by_number(db, level_data.level)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Level already exists"
            )

        level = crud_level.create_level(db, level_data)
        return level

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create level"
        )
'''


@router.put("/{level_number}", response_model=LevelSystemResponse)
def update_level(
    level_number: int,
    level_update: LevelSystemUpdate,
    db: Session = Depends(get_db),
    # current_admin = Depends(get_current_admin_user)  # Add if you have admin auth
):
    """Update level (Admin only)"""
    level = crud_level.update_level(db, level_number, level_update)
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
    success = crud_level.delete_level(db, level_number)
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
    existing = crud_level.get_level_by_number(db, level_data.level)
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
        level = crud_level.create_level(db, level_data)
        return level
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create level: {str(e)}"
        )


'''
# pagination in level system
@router.get("/list")
def get_levels(
    search: Optional[str] = Query(None, description="Search in level name or description"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get levels with search and pagination"""

    query = db.query(LevelSystem)

    # Apply search
    if search:
        search_filter = f"%{search.lower()}%"
        query = query.filter(
            (LevelSystem.level_name.ilike(search_filter)) |
            (LevelSystem.description.ilike(search_filter))
        )

    # Count total
    total = query.count()

    # Pagination
    offset = (page - 1) * per_page
    levels = query.offset(offset).limit(per_page).all()

    # Pagination metadata
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1

    return {
        "message": "Levels retrieved successfully",
        "data": {
            "levels": [
                {
                    "id": lvl.id,
                    "level": lvl.level,
                    "level_name": lvl.level_name,
                    "min_xp_required": lvl.min_xp_required,
                    "max_xp_required": lvl.max_xp_required,
                    "description": lvl.description
                }
                for lvl in levels
            ],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
    }
'''
