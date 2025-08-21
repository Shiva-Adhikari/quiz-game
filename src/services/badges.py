from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any, Tuple
from src.models.badges import Badge, UserBadge
from src.models.quiz_session import QuizSession  # Assuming this exists
from src.schemas.badges import (
    BadgeCreate,
    BadgeProgressResponse,
    UserBadgesSummaryResponse,
    # BadgeNotificationResponse,
    # UserBadgeResponse,
    # BadgeResponse
)
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from fastapi import Depends
from src.utils.db import get_db


logger = logging.getLogger(__name__)


class BadgeService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    # ===============================================================
    # BADGE CREATION OPERATIONS
    # ===============================================================

    def create_badge(self, badge_data: BadgeCreate) -> Badge:
        """Create a new badge using SQLAlchemy 2.0 ORM"""
        badge = Badge(**badge_data.model_dump())
        self.db.add(badge)
        self.db.commit()
        self.db.refresh(badge)
        logger.info(f"Badge '{badge.name}' created with ID {badge.id}")
        return badge

    def create_multiple_badges(self, badges_data: List[BadgeCreate]) -> List[Badge]:
        """Create multiple badges at once using SQLAlchemy 2.0 ORM"""
        created_badges = []

        for badge_data in badges_data:
            badge = Badge(**badge_data.model_dump())
            self.db.add(badge)
            created_badges.append(badge)

        self.db.commit()

        # Refresh all badges to get their IDs
        for badge in created_badges:
            self.db.refresh(badge)

        logger.info(f"Created {len(created_badges)} badges")
        return created_badges

    def get_all_badges(self) -> List[Badge]:
        """Get all badges using SQLAlchemy 2.0 ORM"""
        stmt = select(Badge).where(Badge.is_active).order_by(Badge.created_at.asc())
        result = self.db.execute(stmt)
        return list(result.scalars().all())

    def get_badge_by_id(self, badge_id: int) -> Optional[Badge]:
        """Get single badge by ID using SQLAlchemy 2.0 ORM"""
        stmt = select(Badge).where(Badge.id == badge_id)
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ===============================================================
    # BASIC BADGE OPERATIONS
    # ===============================================================

    def get_user_badges(self, user_id: int) -> List[UserBadge]:
        """Get all badges earned by a user"""
        user_badges = self.db.query(UserBadge).options(
            selectinload(UserBadge.badge)
        ).filter(
            UserBadge.user_id == user_id
        ).order_by(UserBadge.earned_at.desc()).all()
        return user_badges

    def user_has_badge(self, user_id: int, badge_id: int) -> bool:
        """Check if user already has a specific badge"""
        user_badge = self.db.query(UserBadge).filter(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge_id
        ).first()
        return user_badge is not None

    # ===============================================================
    # USER STATISTICS CALCULATION
    # ===============================================================

    def get_user_quiz_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user quiz statistics for badge checking"""

        # Total completed quizzes
        total_quizzes = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == 'completed'
        ).count()

        # Perfect scores (100% correct)
        perfect_scores = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == 'completed',
            QuizSession.correct_answers == QuizSession.total_questions
        ).count()

        # High scores (90%+ accuracy)
        high_scores_query = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == 'completed'
        ).all()

        high_scores = sum(
            1 for quiz in high_scores_query 
            if quiz.total_questions > 0 and (quiz.correct_answers * 100.0 / quiz.total_questions) >= 90
        )

        # Average completion time per question
        time_queries = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == 'completed',
            QuizSession.total_time_seconds > 0
        ).all()

        if time_queries:
            avg_time_per_question = sum(
                quiz.total_time_seconds / quiz.total_questions 
                for quiz in time_queries 
                if quiz.total_questions > 0
            ) / len(time_queries)
        else:
            avg_time_per_question = 999

        # Category-specific stats
        category_queries = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == 'completed',
            QuizSession.category_id.isnot(None)
        ).all()

        category_stats = {}
        for quiz in category_queries:
            if quiz.category_id not in category_stats:
                category_stats[quiz.category_id] = {
                    'total_quizzes': 0,
                    'total_accuracy': 0,
                    'perfect_scores': 0
                }

            category_stats[quiz.category_id]['total_quizzes'] += 1
            if quiz.total_questions > 0:
                accuracy = (quiz.correct_answers * 100.0) / quiz.total_questions
                category_stats[quiz.category_id]['total_accuracy'] += accuracy

                if quiz.correct_answers == quiz.total_questions:
                    category_stats[quiz.category_id]['perfect_scores'] += 1

        # Calculate average accuracy for each category
        for category_id in category_stats:
            if category_stats[category_id]['total_quizzes'] > 0:
                category_stats[category_id]['avg_accuracy'] = (
                    category_stats[category_id]['total_accuracy'] / 
                    category_stats[category_id]['total_quizzes']
                )
            else:
                category_stats[category_id]['avg_accuracy'] = 0
            del category_stats[category_id]['total_accuracy']

        # Current streak calculation
        recent_quizzes = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == 'completed'
        ).order_by(QuizSession.completed_at.desc()).limit(50).all()

        current_streak = 0
        for quiz in recent_quizzes:
            accuracy = (quiz.correct_answers / quiz.total_questions) * 100 if quiz.total_questions > 0 else 0
            if accuracy >= 70:  # 70%+ considered a good score for streak
                current_streak += 1
            else:
                break

        # Difficulty level stats
        difficulty_queries = self.db.query(QuizSession).filter(
            QuizSession.user_id == user_id,
            QuizSession.status == 'completed'
        ).all()

        difficulty_stats = {}
        for quiz in difficulty_queries:
            if quiz.difficulty_level not in difficulty_stats:
                difficulty_stats[quiz.difficulty_level] = {
                    'total_quizzes': 0,
                    'total_accuracy': 0
                }

            difficulty_stats[quiz.difficulty_level]['total_quizzes'] += 1
            if quiz.total_questions > 0:
                accuracy = (quiz.correct_answers * 100.0) / quiz.total_questions
                difficulty_stats[quiz.difficulty_level]['total_accuracy'] += accuracy

        # Calculate average accuracy for each difficulty
        for difficulty in difficulty_stats:
            if difficulty_stats[difficulty]['total_quizzes'] > 0:
                difficulty_stats[difficulty]['avg_accuracy'] = (
                    difficulty_stats[difficulty]['total_accuracy'] / 
                    difficulty_stats[difficulty]['total_quizzes']
                )
            else:
                difficulty_stats[difficulty]['avg_accuracy'] = 0
            del difficulty_stats[difficulty]['total_accuracy']

        return {
            'total_quizzes': total_quizzes,
            'perfect_scores': perfect_scores,
            'high_scores': high_scores,
            'avg_time_per_question': round(avg_time_per_question, 2),
            'current_streak': current_streak,
            'category_stats': category_stats,
            'difficulty_stats': difficulty_stats,
            'quiz_count': total_quizzes,  # Alias for badge criteria
            'perfect_score': perfect_scores,  # Alias for badge criteria
            'speed_average': avg_time_per_question,  # Alias for badge criteria
            'streak_count': current_streak,  # Alias for badge criteria
            'high_score_count': high_scores
        }

    # ===============================================================
    # BADGE CHECKING AND AWARDING
    # ===============================================================

    def check_badge_criteria(self, badge: Badge, user_stats: Dict[str, Any]) -> Tuple[bool, int]:
        """
        Check if user meets badge criteria
        Returns: (meets_criteria: bool, current_progress: int)
        """
        criteria_type = badge.criteria_type
        criteria_value = badge.criteria_value

        if criteria_type == "quiz_count":
            current = user_stats.get('total_quizzes', 0)
            return current >= criteria_value, current

        elif criteria_type == "perfect_score":
            current = user_stats.get('perfect_scores', 0)
            return current >= criteria_value, current

        elif criteria_type == "high_score":
            current = user_stats.get('high_scores', 0)
            return current >= criteria_value, current

        elif criteria_type == "speed_average":
            # For speed badges, lower time is better
            current = user_stats.get('avg_time_per_question', 999)
            return current <= criteria_value, int(current)

        elif criteria_type == "streak_count":
            current = user_stats.get('current_streak', 0)
            return current >= criteria_value, current

        elif criteria_type == "category_accuracy":
            # Category-specific accuracy badge
            if badge.category_id:
                category_data = user_stats.get('category_stats', {}).get(badge.category_id, {})
                current = category_data.get('avg_accuracy', 0)
                return current >= criteria_value, int(current)
            return False, 0

        elif criteria_type == "category_quizzes":
            # Complete X quizzes in specific category
            if badge.category_id:
                category_data = user_stats.get('category_stats', {}).get(badge.category_id, {})
                current = category_data.get('total_quizzes', 0)
                return current >= criteria_value, current
            return False, 0

        elif criteria_type == "difficulty_mastery":
            # Complete X quizzes in specific difficulty
            difficulty_level = {1: 'easy', 2: 'medium', 3: 'hard'}.get(criteria_value, 'easy')
            difficulty_data = user_stats.get('difficulty_stats', {}).get(difficulty_level, {})
            current = difficulty_data.get('total_quizzes', 0)
            return current >= 10, current  # Hardcoded 10 quizzes for mastery

        return False, 0

    def award_badge(self, user_id: int, badge_id: int, progress_value: int = 0) -> UserBadge:
        """Award a badge to a user"""
        # Double-check if user already has this badge
        if self.user_has_badge(user_id, badge_id):
            raise ValueError(f"User {user_id} already has badge {badge_id}")

        user_badge = UserBadge(
            user_id=user_id,
            badge_id=badge_id,
            progress_value=progress_value,
            earned_at=datetime.now(timezone.utc),
            notification_sent=False
        )

        self.db.add(user_badge)
        self.db.commit()
        self.db.refresh(user_badge)

        # Load the badge relationship
        self.db.refresh(user_badge, ["badge"])

        logger.info(f"Badge {badge_id} awarded to user {user_id}")
        return user_badge

    def check_and_award_badges(self, user_id: int) -> List[UserBadge]:
        """Check all badge criteria and award eligible badges"""
        newly_awarded = []

        try:
            # Get user's current stats
            user_stats = self.get_user_quiz_stats(user_id)

            # Get all active badges
            active_badges = self.get_all_badges()

            for badge in active_badges:
                # Skip if user already has this badge
                if self.user_has_badge(user_id, badge.id):
                    continue

                # Check badge criteria
                meets_criteria, current_progress = self.check_badge_criteria(badge, user_stats)

                if meets_criteria:
                    try:
                        awarded_badge = self.award_badge(user_id, badge.id, current_progress)
                        newly_awarded.append(awarded_badge)

                        logger.info(f"Badge '{badge.name}' awarded to user {user_id}")
                    except ValueError as e:
                        logger.warning(f"Failed to award badge {badge.id} to user {user_id}: {e}")
                        continue

            return newly_awarded

        except Exception as e:
            logger.error(f"Error checking badges for user {user_id}: {e}")
            return []

    # ===============================================================
    # PROGRESS TRACKING
    # ===============================================================

    def get_badge_progress(self, user_id: int, badge_id: int) -> BadgeProgressResponse:
        """Get user's progress toward a specific badge"""
        badge = self.get_badge_by_id(badge_id)
        if not badge:
            raise ValueError(f"Badge {badge_id} not found")

        user_stats = self.get_user_quiz_stats(user_id)
        is_earned = self.user_has_badge(user_id, badge_id)

        meets_criteria, current_progress = self.check_badge_criteria(badge, user_stats)
        target_progress = badge.criteria_value

        # Calculate progress percentage
        if badge.criteria_type == "speed_average":
            # For speed badges, lower is better, so reverse the calculation
            if current_progress <= target_progress:
                progress_percentage = 100.0
            else:
                progress_percentage = max(0, (target_progress / current_progress) * 100)
        else:
            progress_percentage = min((current_progress / target_progress) * 100, 100) if target_progress > 0 else 0

        return BadgeProgressResponse(
            badge=badge,
            progress_current=current_progress,
            progress_target=target_progress,
            progress_percentage=round(progress_percentage, 1),
            is_earned=is_earned,
            is_achievable=meets_criteria
        )

    def get_user_badges_summary(self, user_id: int) -> UserBadgesSummaryResponse:
        """Get comprehensive badge summary for a user"""
        # Get earned badges
        earned_badges = self.get_user_badges(user_id)

        # Get all active badges for progress tracking
        all_badges = self.get_all_badges()
        available_badges = []
        next_achievable = None

        for badge in all_badges:
            progress = self.get_badge_progress(user_id, badge.id)

            if not progress.is_earned:
                available_badges.append(progress)

                # Find the badge closest to completion
                if (progress.progress_percentage > 0 and 
                    (next_achievable is None or progress.progress_percentage > next_achievable.progress_percentage)):
                    next_achievable = progress

        # Sort available badges by progress percentage (closest first)
        available_badges.sort(key=lambda x: x.progress_percentage, reverse=True)

        # Calculate totals
        total_xp = sum(badge.badge.xp_reward for badge in earned_badges)
        total_coins = sum(badge.badge.coins_reward for badge in earned_badges)

        return UserBadgesSummaryResponse(
            earned_badges=earned_badges,
            available_badges=available_badges,
            total_earned=len(earned_badges),
            total_xp_from_badges=total_xp,
            total_coins_from_badges=total_coins,
            next_achievable_badge=next_achievable
        )

    # ===============================================================
    # NOTIFICATION SYSTEM
    # ===============================================================

    def get_unnotified_badges(self, user_id: int) -> List[UserBadge]:
        """Get badges that haven't been notified to the user yet"""
        unnotified_badges = self.db.query(UserBadge).options(
            selectinload(UserBadge.badge)
        ).filter(
            UserBadge.user_id == user_id,
            UserBadge.notification_sent == False
        ).all()
        return unnotified_badges

    def mark_badges_notified(self, user_badge_ids: List[int]) -> None:
        """Mark badges as notified"""
        badges_to_update = self.db.query(UserBadge).filter(
            UserBadge.id.in_(user_badge_ids)
        ).all()

        for badge in badges_to_update:
            badge.notification_sent = True

        self.db.commit()
