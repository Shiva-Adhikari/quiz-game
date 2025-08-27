from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from src.models.user_profile import UserProfile
from typing import Tuple, Optional, List
import math


class LeaderboardService:

    @staticmethod
    def get_leaderboard(
        db: Session,
        page: int = 1,
        per_page: int = 10
    ) -> Tuple[List[UserProfile], int, int]:
        """
        Get paginated leaderboard ordered by total_xp
        Returns: (profiles, total_count, total_pages)
        """
        # Calculate offset
        offset = (page - 1) * per_page

        # Get total count
        total_count = db.query(UserProfile).count()
        total_pages = math.ceil(total_count / per_page)

        # Get leaderboard with pagination
        profiles = (
            db.query(UserProfile)
            .order_by(desc(UserProfile.total_xp), desc(UserProfile.created_at))
            .offset(offset)
            .limit(per_page)
            .all()
        )

        return profiles, total_count, total_pages

    @staticmethod
    def get_user_rank(db: Session, user_id: int) -> Optional[Tuple[int, UserProfile]]:
        """
        Get specific user's rank and profile
        Returns: (rank, user_profile) or None if user not found
        """
        # Get user profile
        user_profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

        if not user_profile:
            return None

        # Calculate rank by counting users with higher XP
        rank = (
            db.query(func.count(UserProfile.id))
            .filter(
                (UserProfile.total_xp > user_profile.total_xp) |
                ((UserProfile.total_xp == user_profile.total_xp) & 
                 (UserProfile.created_at < user_profile.created_at))
            )
            .scalar()
        ) + 1

        return rank, user_profile

    @staticmethod
    def get_top_players(db: Session, limit: int = 10) -> List[UserProfile]:
        """
        Get top N players by XP
        """
        return (
            db.query(UserProfile)
            .order_by(desc(UserProfile.total_xp), desc(UserProfile.created_at))
            .limit(limit)
            .all()
        )
