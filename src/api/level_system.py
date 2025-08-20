from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from typing import List
from src.schemas.level_system import LevelSystemResponse, LevelSystemCreate, LevelSystemUpdate
from src.crud import level_system as crud_level
# Using your existing dependencies: get_db, get_current_admin_user (if you have admin)
from src.utils.db import get_db


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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create level"
        )

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
