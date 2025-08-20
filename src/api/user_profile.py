from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from src.schemas.user_profile import UserProfileResponse, UserProfilePublicResponse, UserProfileUpdate
from src.crud import user_profile as crud_profile
from src.utils.user_profile import format_profile_response, validate_display_name
from src.utils.db import get_db
from src.utils.get_current_user import get_current_user
from src.models.authentication import User


router = APIRouter(prefix="/profile", tags=["user_profile"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's complete profile"""
    profile = crud_profile.get_user_profile(db, current_user.id)
    print(f'profile: {profile}')
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Add calculated fields
    profile = format_profile_response(profile, db)
    return profile

@router.get("/{user_id}", response_model=UserProfilePublicResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Get public profile view of any user"""
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    
    profile = crud_profile.get_user_profile(db, user_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Add calculated fields
    profile = format_profile_response(profile, db)
    return profile

@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(profile_update: UserProfileUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update current user's profile"""
    # Validate display name if provided
    if profile_update.display_name and not validate_display_name(profile_update.display_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid display name format. Use only letters, numbers, spaces, and underscores (3-30 characters)"
        )
    
    try:
        profile = crud_profile.update_user_profile(db, current_user.id, profile_update)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Add calculated fields
        profile = format_profile_response(profile, db)
        return profile
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me/rank")
def get_my_rank(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user's global rank"""
    rank = crud_profile.get_user_rank(db, current_user.id)
    return {"rank": rank}

@router.post("/me/stats")
def update_my_stats(
    xp_gained: int = 0,
    coins_gained: int = 0,
    games_played: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile stats (called after quiz completion)"""
    if xp_gained < 0 or coins_gained < 0 or games_played < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Values cannot be negative"
        )
    
    try:
        profile = crud_profile.update_profile_stats(db, current_user.id, xp_gained, coins_gained, games_played)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        # Add calculated fields
        profile = format_profile_response(profile, db)
        return {"message": "Stats updated successfully", "profile": profile}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stats as {e}"
        )
