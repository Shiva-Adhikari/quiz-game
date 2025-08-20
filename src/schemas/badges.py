from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class BadgeBase(BaseModel):
    name: str
    description: str
    criteria_type: str
    criteria_value: int
    category_id: Optional[int] = None
    icon_url: Optional[str] = None
    xp_reward: int = 0
    coins_reward: int = 0


class BadgeCreate(BadgeBase):
    pass


class BadgeResponse(BadgeBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    created_at: datetime


class UserBadgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    badge_id: int
    earned_at: datetime
    progress_value: int
    is_claimed: bool
    notification_sent: bool
    badge: BadgeResponse


class BadgeProgressResponse(BaseModel):
    badge: BadgeResponse
    progress_current: int
    progress_target: int
    progress_percentage: float
    is_earned: bool
    is_achievable: bool  # Can be earned with current stats


class UserBadgesSummaryResponse(BaseModel):
    earned_badges: List[UserBadgeResponse]
    available_badges: List[BadgeProgressResponse]
    total_earned: int
    total_xp_from_badges: int
    total_coins_from_badges: int
    next_achievable_badge: Optional[BadgeProgressResponse] = None


class BadgeNotificationResponse(BaseModel):
    badge_id: int
    badge_name: str
    xp_reward: int
    coins_reward: int
    message: str
