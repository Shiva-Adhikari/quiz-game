from typing import Dict


def calculate_quiz_rewards(
    correct_answers: int,
    total_questions: int,
    difficulty_level: str = "easy",
    category_multiplier: float = 1.0,
    session_type: str = "random"
) -> Dict[str, int]:
    """Calculate XP and coins for quiz completion"""
    
    score_percentage = (correct_answers / total_questions) * 100
    
    # Base rewards
    base_xp_per_percent = 2
    base_coins_per_correct = 10
    
    # Difficulty multipliers
    difficulty_multipliers = {
        "easy": 1.0,
        "medium": 1.2,
        "hard": 1.5,
        "mixed": 1.1
    }
    
    # Session type multipliers
    session_multipliers = {
        "random": 1.0,
        "category": 1.1,
        "timed": 1.3
    }
    
    difficulty_mult = difficulty_multipliers.get(difficulty_level, 1.0)
    session_mult = session_multipliers.get(session_type, 1.0)
    
    final_multiplier = difficulty_mult * category_multiplier * session_mult
    
    xp_earned = int(score_percentage * base_xp_per_percent * final_multiplier)
    coins_earned = int(correct_answers * base_coins_per_correct * final_multiplier)
    
    return {
        "xp_earned": xp_earned,
        "coins_earned": coins_earned,
        "score_percentage": round(score_percentage, 2),
        "multiplier_applied": round(final_multiplier, 2)
    }
