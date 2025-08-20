from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Text
from src.core.database import Base


class LevelSystem(Base):
    __tablename__ = "level_system"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    level_name: Mapped[str] = mapped_column(String(50))
    min_xp_required: Mapped[int] = mapped_column(Integer, index=True)
    max_xp_required: Mapped[int] = mapped_column(Integer, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
