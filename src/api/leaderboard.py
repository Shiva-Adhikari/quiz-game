from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from src.utils.db import get_db
from src.services.leaderboard_service import LeaderboardService
from src.schemas.leaderboard import (
    LeaderboardResponse,
    LeaderboardEntry,
    UserRankResponse
)
from typing import List
import math
from src.models.user_profile import UserProfile
from sqlalchemy import desc

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("/", response_model=LeaderboardResponse)
def get_leaderboard(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated leaderboard ordered by total XP
    """
    try:
        profiles, total_count, total_pages = LeaderboardService.get_leaderboard(
            db=db, page=page, per_page=per_page
        )

        # Calculate ranks and convert to response format
        leaderboard_entries = []
        start_rank = (page - 1) * per_page + 1

        for i, profile in enumerate(profiles):
            entry = LeaderboardEntry(
                rank=start_rank + i,
                user_id=profile.user_id,
                display_name=profile.display_name,
                total_xp=profile.total_xp,
                current_level=profile.current_level,
                total_games_played=profile.total_games_played,
                created_at=profile.created_at
            )
            leaderboard_entries.append(entry)

        return LeaderboardResponse(
            total_players=total_count,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            leaderboard=leaderboard_entries
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leaderboard: {str(e)}")


@router.get("/top/{limit}", response_model=List[LeaderboardEntry])
def get_top_players(
    limit: int = Path(ge=1, le=100, description="Number of top players"),
    db: Session = Depends(get_db)
):
    """
    Get top N players by XP
    """
    try:
        profiles = LeaderboardService.get_top_players(db=db, limit=limit)

        leaderboard_entries = []
        for i, profile in enumerate(profiles):
            entry = LeaderboardEntry(
                rank=i + 1,
                user_id=profile.user_id,
                display_name=profile.display_name,
                total_xp=profile.total_xp,
                current_level=profile.current_level,
                total_games_played=profile.total_games_played,
                created_at=profile.created_at
            )
            leaderboard_entries.append(entry)

        return leaderboard_entries

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top players: {str(e)}")


@router.get("/user/{user_id}/rank", response_model=UserRankResponse)
def get_user_rank(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific user's rank and profile information
    """
    try:
        result = LeaderboardService.get_user_rank(db=db, user_id=user_id)

        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        rank, user_profile = result
        total_players = db.query(UserProfile).count()

        user_entry = LeaderboardEntry(
            rank=rank,
            user_id=user_profile.user_id,
            display_name=user_profile.display_name,
            total_xp=user_profile.total_xp,
            current_level=user_profile.current_level,
            total_games_played=user_profile.total_games_played,
            created_at=user_profile.created_at
        )

        return UserRankResponse(
            user_rank=rank,
            total_players=total_players,
            user_profile=user_entry
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user rank: {str(e)}")


@router.get("/around-user/{user_id}", response_model=List[LeaderboardEntry])
def get_leaderboard_around_user(
    user_id: int,
    radius: int = Query(5, ge=1, le=25, description="Number of players above and below"),
    db: Session = Depends(get_db)
):
    """
    Get leaderboard entries around a specific user
    """
    try:
        # Get user's rank first
        result = LeaderboardService.get_user_rank(db=db, user_id=user_id)
        if not result:
            raise HTTPException(status_code=404, detail="User not found")

        user_rank, _ = result

        # Calculate the range
        start_rank = max(1, user_rank - radius)
        total_to_fetch = radius * 2 + 1

        # Calculate page parameters
        page = math.ceil(start_rank / total_to_fetch)

        # Get profiles around the user
        profiles = (
            db.query(UserProfile)
            .order_by(desc(UserProfile.total_xp), desc(UserProfile.created_at))
            .offset(start_rank - 1)
            .limit(total_to_fetch)
            .all()
        )

        leaderboard_entries = []
        for i, profile in enumerate(profiles):
            entry = LeaderboardEntry(
                rank=start_rank + i,
                user_id=profile.user_id,
                display_name=profile.display_name,
                total_xp=profile.total_xp,
                current_level=profile.current_level,
                total_games_played=profile.total_games_played,
                created_at=profile.created_at
            )
            leaderboard_entries.append(entry)

        return leaderboard_entries

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leaderboard around user: {str(e)}")
