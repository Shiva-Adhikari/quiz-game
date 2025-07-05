# Standard library imports
from enum import Enum
from typing import Optional
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, Boolean, DateTime, String, func, ForeignKey,
    CheckConstraint, Enum as SQLEnum)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.questions import Category, DifficultyLevel
from src.models.authentication import User


class RoomStatus(str, Enum):
    STARTING = 'starting'
    ACTIVE = 'active'
    WAITING = 'waiting'
    FINISHED = 'finished'
    CANCELLED = 'cancelled'


class RoomType(str, Enum):
    SYSTEM_CREATED = 'system_created'
    USER_CREATED = 'user_created'
    TOURNAMENT = 'tournament'
    PRIVATE = 'private'


class MultiplayerRoom(Base):
    __tablename__ = 'multiplayer_rooms'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'), index=True)
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    room_name: Mapped[str] = mapped_column(String(100), nullable=False)
    room_code: Mapped[int] = mapped_column(
        Integer, nullable=True, unique=True, index=True)
    room_type: Mapped[RoomType] = mapped_column(
        SQLEnum(RoomType), default=RoomType.SYSTEM_CREATED.value)
    max_players: Mapped[int] = mapped_column(Integer, default=0)
    current_players: Mapped[int] = mapped_column(Integer, default=0)
    difficulty_level: Mapped[DifficultyLevel] = mapped_column(
        SQLEnum(DifficultyLevel), nullable=False,
        default=DifficultyLevel.EASY.value)
    status: Mapped[RoomStatus] = mapped_column(
        SQLEnum(RoomStatus), nullable=False)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    auto_start_threshold: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped['User'] = relationship(
        'User', back_populates='multiplayer_rooms')
    category: Mapped['Category'] = relationship(
        'Category', back_populates='multiplayer_rooms')

    # Constaints
    __table_args__ = (
        CheckConstraint(
            'max_players >= 0', name='check_max_players_non_negative'),
        CheckConstraint(
            'current_players >= 0', name='check_current_players_non_negative')
    )

    def __repr__(self) -> str:
        return (
            f"<MultiplayerRoom(id={self.id}, "
            f"room_name='{self.room_name}', "
            f"room_code='{self.room_code}', "
            f"status='{self.status}', "
            f"current_players={self.current_players}/{self.max_players})>"
        )


class RoomParticipant(Base):
    __tablename__ = 'room_participants'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('multiplayer_rooms.id'), index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    is_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    current_score: Mapped[int] = mapped_column(Integer, default=0)
    player_skill_rating: Mapped[int] = mapped_column(Integer, default=0)
    join_method: Mapped[str] = mapped_column(String, nullable=False)


class MatchmakingQueue(Base):
    __tablename__ = 'matchmaking_queue'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    preferred_category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'), index=True)
    preferred_difficulty: Mapped[str] = mapped_column(String, nullable=False)
    skill_rating: Mapped[int] = mapped_column(Integer, default=0)
    queue_joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    estimated_wait_time: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False)
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)


class MatchmakingCriteria(Base):
    __tablename__ = 'matchmaking_criteria'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'), index=True)
    min_players: Mapped[int] = mapped_column(Integer, default=0)
    max_players: Mapped[int] = mapped_column(Integer, default=0)
    skill_range_tolerance: Mapped[int] = mapped_column(Integer, default=0)
    difficulty_level: Mapped[str] = mapped_column(String, nullable=False)
    max_wait_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())


class SkillRating(Base):
    __tablename__ = 'skill_ratings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    current_rating: Mapped[int] = mapped_column(Integer, default=0)
    peak_rating: Mapped[int] = mapped_column(Integer, default=0)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    wins: Mapped[int] = mapped_column(Integer, default=0)
    losses: Mapped[int] = mapped_column(Integer, default=0)
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    rating_volatility: Mapped[int] = mapped_column(Integer, default=0)


class RoomInvitation(Base):
    __tablename__ = 'room_invitations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('multiplayer_rooms.id'), index=True)
    inviter_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    invited_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    invitation_code: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    send_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)


class MatchmakingSessions(Base):
    __tablename__ = 'matchmaking_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('sessions.id'), index=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('multiplayer_rooms.id'), index=True)
    initiated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True)
    players_matched: Mapped[int] = mapped_column(Integer, default=0)
    average_skill_rating: Mapped[int] = mapped_column(Integer, default=0)
    match_quality_score: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)


class AutoRoomSetting(Base):
    __tablename__ = 'auto_room_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # default_category_id:
    room_type: Mapped[str] = mapped_column(String, nullable=False)
    default_max_players: Mapped[int] = mapped_column(Integer, default=0)
    default_difficulty: Mapped[str] = mapped_column(String, nullable=False)
    auto_start_delay_seconds: Mapped[int] = mapped_column(Integer, default=0)
    skill_matching_enabled: Mapped[bool] = mapped_column(
        Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())
