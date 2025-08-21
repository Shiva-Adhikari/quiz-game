from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional
from datetime import datetime


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=3, max_length=30)

    @validator('display_name')
    def validate_display_name(cls, v):
        if v is not None:
            if not v.replace(" ", "").replace("_", "").isalnum():
                raise ValueError('Display name can only contain letters, numbers, spaces, and underscores')
        return v


class LevelInfoResponse(BaseModel):
    level: int
    level_name: str
    min_xp_required: int
    max_xp_required: int
    xp_progress: int
    xp_needed_for_next: int

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    id: int
    user_id: int
    display_name: str
    total_xp: int
    current_level: int
    coins: int
    total_games_played: int
    created_at: datetime
    updated_at: datetime
    level_info: Optional[LevelInfoResponse] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfilePublicResponse(BaseModel):
    id: int
    display_name: str
    current_level: int
    total_xp: int
    total_games_played: int
    level_info: Optional[LevelInfoResponse] = None

    model_config = ConfigDict(from_attributes=True)
