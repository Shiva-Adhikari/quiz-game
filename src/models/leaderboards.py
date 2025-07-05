# Standard library imports
from datetime import datetime

# Third-party imports
from sqlalchemy import (
    Integer, DateTime, ForeignKey, Float, CheckConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Local imports
from src.core import Base
from src.models.questions import Category
from src.models.authentication import User


class Leaderboards(Base):
    __tablename__ = 'leaderboards'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'), index=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    rank_position: Mapped[int] = mapped_column(Integer, default=0)
    games_played: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float] = mapped_column(Float, default=0.0)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False)

    # Relationship
    user: Mapped['User'] = relationship(
        'User', back_populates='leaderboards')
    category: Mapped['Category'] = relationship(
        'Category', back_populates='leaderboards')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'total_score >= 0', name='check_total_score_non_negative'),
        CheckConstraint(
            'rank_position >= 0', name='check_rank_position_non_negative'),
        CheckConstraint(
            'games_played >= 0', name='check_games_played_non_negative'),
        CheckConstraint(
            'accuracy >= 0 AND accuracy <= 100', name='check_accuracy_range'),
    )

    def __repr__(self) -> str:
        return f'<Leaderboards(id={self.id}, user_id={self.user_id}, ' \
            f'category_id={self.category_id}, rank={self.rank_position}, ' \
            f'score={self.total_score})>'


class RankingHistory(Base):
    __tablename__ = 'ranking_histories'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id'), index=True)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('categories.id'), index=True)
    rank_position: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    user: Mapped['User'] = relationship(
        'User', back_populates='ranking_histories')
    category: Mapped['Category'] = relationship(
        'Category', back_populates='ranking_histories')

    # Constraints
    __table_args__ = (
        CheckConstraint(
            'rank_position', name='check_rank_position_non_negative'),
        CheckConstraint('total_score', name='check_total_score_non_negative'),
    )

    def __repr__(self) -> str:
        return f'<RankingHistory(id={self.id}, user_id={self.user_id}, ' \
            f'category_id={self.category_id}, rank={self.rank_position}, ' \
            f'score={self.total_score}, recorded_at={self.recorded_at})>'
# /
