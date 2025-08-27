from pydantic import BaseModel, Field
from datetime import datetime
from typing import List


class LeaderboardEntry(BaseModel):
    rank: int = Field(..., description="Player's rank position")
    user_id: int
    display_name: str
    total_xp: int
    current_level: int
    total_games_played: int
    created_at: datetime

    class Config:
        from_attributes = True


class LeaderboardResponse(BaseModel):
    total_players: int
    page: int
    per_page: int
    total_pages: int
    leaderboard: List[LeaderboardEntry]


class UserRankResponse(BaseModel):
    user_rank: int
    total_players: int
    user_profile: LeaderboardEntry
