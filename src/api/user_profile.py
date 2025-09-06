from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from src.schemas.user_profile import UserProfileResponse, UserProfilePublicResponse, UserProfileUpdate
from src.crud import user_profile as crud_profile
from src.utils.user_profile import format_profile_response, validate_display_name
from src.utils.db import get_db
from src.utils.get_current_user import get_current_user
from src.models.authentication import User

router = APIRouter(prefix="/profile", tags=["user_profile"])


@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    """Get current user's complete profile"""
    try:
        profile = crud_profile.get_user_profile(db, current_user.id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        # Import your level system function
        from src.utils.level_system import get_level_from_xp

        # Get level information
        level_info = get_level_from_xp(db, profile.total_xp)

        # Calculate progress within current level
        current_xp_in_level = profile.total_xp - level_info["min_xp"]

        # Format response with level data
        formatted_profile = {
            "id": profile.id,
            "user_id": profile.user_id,
            "display_name": profile.display_name,
            "total_xp": profile.total_xp,
            "current_level": level_info["level"],
            "coins": profile.coins,
            "total_games_played": profile.total_games_played,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
            "level_info": {
                "level": level_info["level"],
                "level_name": level_info["level_name"],
                "min_xp_required": level_info["min_xp"],
                "max_xp_required": level_info["max_xp"],
                "xp_progress": current_xp_in_level,
                "xp_needed_for_next": level_info["xp_to_next_level"]
            }
        }

        return formatted_profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserProfilePublicResponse)
def get_user_profile(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)  # Optional for public access
):
    """Get public profile view of any user"""
    if user_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    try:
        profile = crud_profile.get_user_profile(db, user_id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        # Check if profile is private and user is not authenticated
        if hasattr(profile, 'is_private') and profile.is_private and not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to view private profile"
            )

        # Check if profile is private and user is not the owner or friend
        if (hasattr(profile, 'is_private') and profile.is_private and 
            current_user and current_user.id != user_id):
            # You can add friend check logic here
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view private profile"
            )

        # Add calculated fields
        profile = format_profile_response(profile, db)
        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(
    profile_update: UserProfileUpdate, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    """Update current user's profile"""
    # Validate display name if provided
    if profile_update.display_name and not validate_display_name(profile_update.display_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid display name format. Use only letters, numbers, spaces, and underscores (3-30 characters)"
        )

    try:
        # Check if user is verified for certain profile updates
        if not current_user.is_verified:
            # Restrict certain updates for unverified users
            restricted_fields = ['bio', 'location', 'website']
            update_dict = profile_update.dict(exclude_unset=True)

            for field in restricted_fields:
                if field in update_dict and update_dict[field]:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Email verification required to update {field}"
                    )

        profile = crud_profile.update_user_profile(db, current_user.id, profile_update)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        # Add calculated fields
        profile = format_profile_response(profile, db)
        return profile

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/me/rank")
def get_my_rank(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """Get current user's global rank"""
    try:
        rank = crud_profile.get_user_rank(db, current_user.id)

        if rank is None:
            return {
                "rank": None,
                "message": "Rank not available - complete some quizzes first!"
            }

        return {
            "rank": rank,
            "user_id": current_user.id,
            "username": current_user.username
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rank: {str(e)}"
        )


@router.post("/me/stats")
def update_my_stats(
    xp_gained: int = 0,
    coins_gained: int = 0,
    games_played: int = 1,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    """Update profile stats (called after quiz completion)"""
    # Validation
    if xp_gained < 0 or coins_gained < 0 or games_played < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Values cannot be negative"
        )

    # Reasonable limits to prevent abuse
    if xp_gained > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="XP gained exceeds maximum allowed (10,000)"
        )

    if coins_gained > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coins gained exceeds maximum allowed (5,000)"
        )

    if games_played > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Games played exceeds maximum allowed (100)"
        )

    try:
        # Check if user is verified
        if not current_user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email verification required to update stats"
            )

        profile = crud_profile.update_profile_stats(
            db, current_user.id, xp_gained, coins_gained, games_played
        )

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        # Add calculated fields
        profile = format_profile_response(profile, db)

        # Detect client type for analytics
        is_mobile = user_agent and ('okhttp' in user_agent.lower() or 'android' in user_agent.lower() or 'ios' in user_agent.lower())

        return {
            "message": "Stats updated successfully",
            "profile": profile,
            "updates": {
                "xp_gained": xp_gained,
                "coins_gained": coins_gained,
                "games_played": games_played
            },
            "client_type": "mobile" if is_mobile else "web"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update stats: {str(e)}"
        )


@router.get("/me/summary")
def get_profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a quick summary of user's profile stats"""
    try:
        profile = crud_profile.get_user_profile(db, current_user.id)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        rank = crud_profile.get_user_rank(db, current_user.id)

        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "display_name": getattr(profile, 'display_name', None),
            "total_xp": getattr(profile, 'total_xp', 0),
            "coins": getattr(profile, 'coins', 0),
            "games_played": getattr(profile, 'games_played', 0),
            "rank": rank,
            "level": getattr(profile, 'level', 1),
            "is_verified": current_user.is_verified
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile summary: {str(e)}"
        )


@router.delete("/me")
def delete_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft delete user profile (deactivate account)"""
    try:
        # Instead of hard delete, mark as inactive
        current_user.is_active = False
        db.commit()

        return {
            "message": "Profile deactivated successfully",
            "note": "Your account has been deactivated. Contact support to reactivate."
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate profile: {str(e)}"
        )
