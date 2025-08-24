from sqlalchemy import Integer, String, DateTime, Boolean, Float, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from src.core.database import Base
# from src.models.questions import Category
# from src.models.authentication import User


class MultiplayerRoom(Base):
    __tablename__ = "multiplayer_rooms"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    room_name: Mapped[str] = mapped_column(String(100))
    host_user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), index=True)  # ForeignKey to User
    max_players: Mapped[int] = mapped_column(Integer, default=4)
    current_players: Mapped[int] = mapped_column(Integer, default=0)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('categories.id'), nullable=True, index=True)  # ForeignKey to Category
    difficulty_level: Mapped[str] = mapped_column(String(20), default="medium")
    total_questions: Mapped[int] = mapped_column(Integer, default=10)
    time_per_question: Mapped[int] = mapped_column(Integer, default=30)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    room_password: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="waiting")  # waiting, in_progress, finished
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    participants: Mapped[List["RoomParticipant"]] = relationship("RoomParticipant", back_populates="room")
    game_sessions: Mapped[List["GameSession"]] = relationship("GameSession", back_populates="room")


class RoomParticipant(Base):
    __tablename__ = "room_participants"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("multiplayer_rooms.id"))
    user_id: Mapped[int] = mapped_column(Integer)  # ForeignKey to User
    is_ready: Mapped[bool] = mapped_column(Boolean, default=False)
    is_host: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Game stats
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0)
    wrong_answers: Mapped[int] = mapped_column(Integer, default=0)
    average_time: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Relationships
    room: Mapped["MultiplayerRoom"] = relationship("MultiplayerRoom", back_populates="participants")
    answers: Mapped[List["PlayerAnswer"]] = relationship("PlayerAnswer", back_populates="participant")


class GameSession(Base):
    __tablename__ = "game_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("multiplayer_rooms.id"))
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, finished
    
    # Question management
    selected_questions: Mapped[str] = mapped_column(Text)  # JSON string of question IDs
    
    # Relationships
    room: Mapped["MultiplayerRoom"] = relationship("MultiplayerRoom", back_populates="game_sessions")
    answers: Mapped[List["PlayerAnswer"]] = relationship("PlayerAnswer", back_populates="game_session")


class PlayerAnswer(Base):
    __tablename__ = "player_answers"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    game_session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id"))
    participant_id: Mapped[int] = mapped_column(ForeignKey("room_participants.id"))
    question_id: Mapped[int] = mapped_column(Integer)  # Reference to Question
    selected_answer: Mapped[str] = mapped_column(String(10))  # A, B, C, D
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    time_taken: Mapped[float] = mapped_column(Float)  # seconds
    score_earned: Mapped[int] = mapped_column(Integer, default=0)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    game_session: Mapped["GameSession"] = relationship("GameSession", back_populates="answers")
    participant: Mapped["RoomParticipant"] = relationship("RoomParticipant", back_populates="answers")
