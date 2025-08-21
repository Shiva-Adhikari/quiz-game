from sqlalchemy.orm import Session
from src.models.level_system import LevelSystem
from src.crud.level_system import create_level
from src.schemas.level_system import LevelSystemCreate
from sqlalchemy import select


def initialize_level_system(db: Session):
    """Initialize the level system with default levels"""

    # Check if levels already exist
    existing_levels = db.scalars(select(LevelSystem)).first()
    if existing_levels:
        print("Level system already initialized")
        return

    # Define default levels
    default_levels = [
        {"level": 1, "level_name": "Beginner", "min_xp_required": 0, "max_xp_required": 99, "description": "Starting your quiz journey"},
        {"level": 2, "level_name": "Novice", "min_xp_required": 100, "max_xp_required": 249, "description": "Learning the basics"},
        {"level": 3, "level_name": "Apprentice", "min_xp_required": 250, "max_xp_required": 499, "description": "Building knowledge"},
        {"level": 4, "level_name": "Student", "min_xp_required": 500, "max_xp_required": 799, "description": "Developing skills"},
        {"level": 5, "level_name": "Scholar", "min_xp_required": 800, "max_xp_required": 1199, "description": "Gaining expertise"},
        {"level": 6, "level_name": "Expert", "min_xp_required": 1200, "max_xp_required": 1699, "description": "Demonstrating mastery"},
        {"level": 7, "level_name": "Master", "min_xp_required": 1700, "max_xp_required": 2299, "description": "Achieving excellence"},
        {"level": 8, "level_name": "Grandmaster", "min_xp_required": 2300, "max_xp_required": 2999, "description": "Reaching new heights"},
        {"level": 9, "level_name": "Champion", "min_xp_required": 3000, "max_xp_required": 3999, "description": "Standing among the best"},
        {"level": 10, "level_name": "Legend", "min_xp_required": 4000, "max_xp_required": 5499, "description": "Legendary status achieved"},
        {"level": 11, "level_name": "Elite", "min_xp_required": 5500, "max_xp_required": 7499, "description": "Elite performer"},
        {"level": 12, "level_name": "Supreme", "min_xp_required": 7500, "max_xp_required": 9999, "description": "Supreme knowledge"},
        {"level": 13, "level_name": "Ultimate", "min_xp_required": 10000, "max_xp_required": 14999, "description": "Ultimate achievement"},
        {"level": 14, "level_name": "Transcendent", "min_xp_required": 15000, "max_xp_required": 24999, "description": "Transcending limits"},
        {"level": 15, "level_name": "Omniscient", "min_xp_required": 25000, "max_xp_required": 999999999, "description": "All-knowing quiz master"}
    ]

    # Create levels
    try:
        for level_data in default_levels:
            level_create = LevelSystemCreate(**level_data)
            create_level(db, level_create)

        print(f"Successfully initialized {len(default_levels)} levels")

    except Exception as e:
        print(f"Error initializing level system: {e}")
        db.rollback()
        raise
