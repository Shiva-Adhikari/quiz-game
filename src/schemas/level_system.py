from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class LevelSystemBase(BaseModel):
    level: int
    level_name: str
    min_xp_required: int
    max_xp_required: int
    description: Optional[str] = None


class LevelSystemCreate(LevelSystemBase):
    pass


class LevelSystemUpdate(BaseModel):
    level_name: Optional[str] = None
    min_xp_required: Optional[int] = None
    max_xp_required: Optional[int] = None
    description: Optional[str] = None


class LevelSystemResponse(LevelSystemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class BulkLevelCreate(BaseModel):
    levels: List[LevelSystemCreate]
