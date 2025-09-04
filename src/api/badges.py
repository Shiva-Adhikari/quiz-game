from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from src.services.badges import BadgeService
from src.schemas.badges import (
    BadgeCreate,
    BadgeResponse,
    UserBadgeResponse,
    BadgeProgressResponse,
    UserBadgesSummaryResponse,
    BadgeNotificationResponse
)
from src.utils.db import get_db  # Your database dependency

router = APIRouter(prefix="/badges", tags=["badges"])


def get_badge_service(db: Session = Depends(get_db)) -> BadgeService:
    return BadgeService(db)


@router.post("/create-badge", response_model=BadgeResponse, status_code=status.HTTP_201_CREATED)
def create_badge(
    badge_data: BadgeCreate,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Create a single badge using SQLAlchemy 2.0 ORM"""
    try:
        badge = badge_service.create_badge(badge_data)
        return badge
    except Exception:
        # logger.error(f"Error creating badge: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create badge"
        )


@router.post("/create-badges/bulk", response_model=List[BadgeResponse], status_code=status.HTTP_201_CREATED)
def create_multiple_badges(
    badges_data: List[BadgeCreate],
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Create multiple badges at once using SQLAlchemy 2.0 ORM"""
    try:
        badges = badge_service.create_multiple_badges(badges_data)
        return badges
    except Exception:
        # logger.error(f"Error creating badges: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create badges"
        )


@router.get("/get_all_badges", response_model=List[BadgeResponse])
def get_all_badges(
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Get all available badges"""
    badges = badge_service.get_all_badges()
    return badges


@router.get("/{badge_id}", response_model=BadgeResponse)
def get_badge(
    badge_id: int,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Get single badge by ID"""
    badge = badge_service.get_badge_by_id(badge_id)
    if not badge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Badge not found"
        )
    return badge


@router.get("/user/{user_id}", response_model=UserBadgesSummaryResponse)
def get_user_badges_summary(
    user_id: int,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Get comprehensive badge summary for user"""
    summary = badge_service.get_user_badges_summary(user_id)
    return summary


@router.get("/user/{user_id}/earned", response_model=List[UserBadgeResponse])
def get_user_earned_badges(
    user_id: int,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Get only badges earned by user"""
    earned_badges = badge_service.get_user_badges(user_id)
    return earned_badges


@router.get("/user/{user_id}/progress/{badge_id}", response_model=BadgeProgressResponse)
def get_badge_progress(
    user_id: int,
    badge_id: int,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Get user's progress toward specific badge"""
    try:
        progress = badge_service.get_badge_progress(user_id, badge_id)
        return progress
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/user/{user_id}/check")
def check_and_award_badges(
    user_id: int,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Check and award eligible badges for user"""
    newly_awarded = badge_service.check_and_award_badges(user_id)

    return {
        "message": f"Checked badges for user {user_id}",
        "badges_awarded": len(newly_awarded),
        "new_badges": [
            {
                "id": badge.badge_id,
                "name": badge.badge.name,
                "xp_reward": badge.badge.xp_reward,
                "coins_reward": badge.badge.coins_reward
            }
            for badge in newly_awarded
        ]
    }


@router.get("/user/{user_id}/notifications", response_model=List[BadgeNotificationResponse])
def get_badge_notifications(
    user_id: int,
    badge_service: BadgeService = Depends(get_badge_service)
):
    """Get unnotified badges for user"""
    unnotified_badges = badge_service.get_unnotified_badges(user_id)

    notifications = []
    for user_badge in unnotified_badges:
        notifications.append(BadgeNotificationResponse(
            badge_id=user_badge.badge_id,
            badge_name=user_badge.badge.name,
            xp_reward=user_badge.badge.xp_reward,
            coins_reward=user_badge.badge.coins_reward,
            message=f"Congratulations! You've earned the '{user_badge.badge.name}' badge!"
        ))

    # === Mark as notified ===
    if unnotified_badges:
        badge_ids = [badge.id for badge in unnotified_badges]
        badge_service.mark_badges_notified(badge_ids)

    return notifications
