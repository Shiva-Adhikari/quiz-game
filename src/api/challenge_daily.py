# === Standard library imports ===
import random
import hashlib
from datetime import date, datetime, timezone

# === Third-party imports ===
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

# === Local imports ===
from src.utils.db import get_db
from src.models.questions import Question
from src.models.authentication import User
from src.utils.get_current_user import get_current_user
from src.schemas.challenge_daily import AnswerSubmissionRequest
from src.models.challenge_daily import DailyChallenge, UserChallengeAttempt, ChallengeStatus


router = APIRouter(prefix='/DailyChallenge', tags=['DailyChallenge'])


def challenges_details() -> dict:
    return {
        'survival_mode': {
            'name': 'Survival Mode',
            'description': 'Keep playing until you get 3 questions wrong',
            'difficulty': 'medium',
            'estimated_time': '5-10 minutes'
        },
        'perfect_score': {
            'name': 'Perfect Score',
            'description': 'Get 100% accuracy on today\'s quiz',
            'difficulty': 'hard',
            'estimated_time': '5 minutes'
        },
        'speed_challenge': {
            'name': 'Speed Challenge',
            'description': 'Answer 10 questions in under 2 minutes',
            'difficulty': 'medium',
            'estimated_time': '2 minutes'
        },
        'lightning_round': {
            'name': 'Lightning Round',
            'description': 'Answer as many questions as possible in 60 seconds',
            'difficulty': 'easy',
            'estimated_time': '1 minute'
        },
        'streak_target': {
            'name': 'Streak Target',
            'description': 'Maintain a 5-question streak',
            'difficulty': 'easy',
            'estimated_time': '3 minutes'
        },
        'marathon_mode': {
            'name': 'Marathon Mode',
            'description': 'Complete a 25-question endurance quiz',
            'difficulty': 'hard',
            'estimated_time': '10-15 minutes'
        }
    }


def challenge_weights() -> dict:
    return {
        'survival_mode': 15,
        'perfect_score': 10,
        'speed_challenge': 20,
        'lightning_round': 25,
        'streak_target': 20,
        'marathon_mode': 10
    }


def get_today_challenge_type() -> str:
    target_date = date.today()

    date_string = target_date.strftime('%Y-%m-%d')
    seed = int(hashlib.md5(date_string.encode()).hexdigest()[:8], 16)

    random.seed(seed)

    challenges = list(challenge_weights().keys())
    weights = list(challenge_weights().values())

    selected_challenge = random.choices(challenges, weights=weights, k=1)[0]    # select 1 item, k=1

    # === Reset random seed ===
    random.seed()

    return selected_challenge


def get_challenge_info(challenge_type: str) -> dict:
    """Get detail information about a specific challenge"""
    challenges = challenges_details()
    return challenges.get(challenge_type, {})


# ########################### SURVIVAL MODE ############################
def get_daily_schedule():
    """Get today schedule date"""
    today = date.today()
    challenge = get_today_challenge_type()
    # challenge = 'survival_mode'
    return {today.strftime("%Y-%m-%d"): challenge}


def difficulty_weights() -> dict:
    return {
        'easy': 50,
        'medium': 30,
        'hard': 20
    }


def get_weighted_difficulty() -> str:
    difficulties = list(difficulty_weights().keys())
    weights = list(difficulty_weights().values())
    return random.choices(difficulties, weights=weights, k=1)[0]


def get_random_question(db: Session) -> Question:
    query = db.query(Question).filter(Question.is_active)
    return query.order_by(func.random()).first()


def get_today_challenge(db: Session):
    """Get today daily challenge record from database"""
    today = date.today()
    result = db.query(DailyChallenge).filter(
        DailyChallenge.challenge_date == today,
        DailyChallenge.is_active
    ).first()

    print(f"\n\n\n\n\nFound daily challenge: {result}")  # Debug print
    return result


def get_or_create_user_attempt(db: Session, user_id: int, daily_challenge_id: int):
    """Get today's daily challenge record from database"""

    attempt = db.query(UserChallengeAttempt).filter(
        UserChallengeAttempt.user_id == user_id,
        UserChallengeAttempt.daily_challenge_id == daily_challenge_id
    ).first()

    if not attempt:
        attempt = UserChallengeAttempt(
            user_id=user_id,
            daily_challenge_id=daily_challenge_id,
            status=ChallengeStatus.NOT_STARTED,
            started_at=datetime.now(timezone.utc)
        )
        db.add(attempt)
        db.flush()
        db.commit()

    return attempt


def create_survival_mode_session(db: Session, user_id: int):
    """Create a new survival mode daily challenge session"""

    # === Get today's challenge or create it ===
    daily_challenge = get_today_challenge(db)
    if not daily_challenge:
        daily_challenge = DailyChallenge(
            challenge_date=date.today(),
            challenge_type='survival_mode',
            is_active=True
        )
        db.add(daily_challenge)
        db.flush()
        db.commit()

    # === Get or create user attempt ===
    user_attempt = get_or_create_user_attempt(db, user_id, daily_challenge.id)

    # === If user already completed today's challenge ===
    if user_attempt.is_completed:
        return {
            'error': "You have already completed today's daily challenge",
            'attempt': user_attempt
        }

    # === ADD THIS RETURN STATEMENT: ===
    return {
        'daily_challenge': daily_challenge,
        'user_attempt': user_attempt
    }


def survival_mode(db: Session, current_user: User):
    """Get survival mode challenge"""

    # === Create daily challenge session ===
    session_data = create_survival_mode_session(db, current_user.id)

    # === Check if user already completed ===
    if "error" in session_data:
        return session_data

    # === Get first question ===
    question = get_random_question(db)
    if not question:
        raise HTTPException(status_code=404, detail='No questions available')

    return {
        'challenge_id': session_data['daily_challenge'].id,
        'attempt_id': session_data['user_attempt'].id,
        'challenge_type': 'survival_mode',
        'challenge_info': get_challenge_info('survival_mode'),
        'status': session_data['user_attempt'].status.value,
        'lives_remaining': 3 - session_data['user_attempt'].wrong_answers,
        'user_attempt': session_data['user_attempt'],
        'questions_answered': session_data['user_attempt'].questions_answered,
        'correct_answers': session_data['user_attempt'].correct_answers,
        'question': {
            'id': question.id,
            'text': question.question_text,  # Add this if available
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }
        }
    }


# ############################ END SURVIVAL MODE ############################

# ############################ OTHER MODE ############################

def perfect_score_mode(db: Session, current_user: User):
    """Start perfect score challenge - 100% accuracy on 10 questions"""

    # === Create daily challenge session ===
    session_data = create_challenge_session(db, current_user.id, 'perfect_score')

    # === Check if user already completed ===
    if "error" in session_data:
        return session_data

    # === Get first question ===
    question = get_random_question(db)
    if not question:
        raise HTTPException(status_code=404, detail='No questions available')

    return {
        'challenge_id': session_data['daily_challenge'].id,
        'attempt_id': session_data['user_attempt'].id,
        'challenge_type': 'perfect_score',
        'challenge_info': get_challenge_info('perfect_score'),
        'status': session_data['user_attempt'].status.value,
        'questions_remaining': 10 - session_data['user_attempt'].questions_answered,
        'progress': f"{session_data['user_attempt'].questions_answered}/10",
        'current_streak': session_data['user_attempt'].current_streak,
        'questions_answered': session_data['user_attempt'].questions_answered,
        'correct_answers': session_data['user_attempt'].correct_answers,
        'accuracy_required': 100,
        'current_accuracy': session_data['user_attempt'].accuracy_percentage,
        'question': {
            'id': question.id,
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }
        }
    }


def speed_challenge_mode(db: Session, current_user: User):
    """Start speed challenge - 10 questions in 2 minutes"""

    # === Create daily challenge session ===
    session_data = create_challenge_session(db, current_user.id, 'speed_challenge')

    # === Check if user already completed ===
    if "error" in session_data:
        return session_data

    # === Get first question ===
    question = get_random_question(db)
    if not question:
        raise HTTPException(status_code=404, detail='No questions available')

    # === Calculate time remaining if already started ===
    time_remaining = 120  # 2 minutes default
    if session_data['user_attempt'].started_at:
        time_elapsed = (datetime.now(timezone.utc) - session_data['user_attempt'].started_at).total_seconds()
        time_remaining = max(0, 120 - time_elapsed)

    return {
        'challenge_id': session_data['daily_challenge'].id,
        'attempt_id': session_data['user_attempt'].id,
        'challenge_type': 'speed_challenge',
        'challenge_info': get_challenge_info('speed_challenge'),
        'status': session_data['user_attempt'].status.value,
        'time_limit_seconds': 120,
        'time_remaining': time_remaining,
        'questions_target': 10,
        'questions_remaining': 10 - session_data['user_attempt'].questions_answered,
        'progress': f"{session_data['user_attempt'].questions_answered}/10",
        'current_streak': session_data['user_attempt'].current_streak,
        'questions_answered': session_data['user_attempt'].questions_answered,
        'correct_answers': session_data['user_attempt'].correct_answers,
        'question': {
            'id': question.id,
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }
        }
    }


def lightning_round_mode(db: Session, current_user: User):
    """Start lightning round - as many questions as possible in 60 seconds"""

    # === Create daily challenge session ===
    session_data = create_challenge_session(db, current_user.id, 'lightning_round')

    # === Check if user already completed ===
    if "error" in session_data:
        return session_data

    # === Get first question ===
    question = get_random_question(db)
    if not question:
        raise HTTPException(status_code=404, detail='No questions available')

    # === Calculate time remaining if already started ===
    time_remaining = 60  # 1 minute default
    if session_data['user_attempt'].started_at:
        time_elapsed = (datetime.now(timezone.utc) - session_data['user_attempt'].started_at).total_seconds()
        time_remaining = max(0, 60 - time_elapsed)

    return {
        'challenge_id': session_data['daily_challenge'].id,
        'attempt_id': session_data['user_attempt'].id,
        'challenge_type': 'lightning_round',
        'challenge_info': get_challenge_info('lightning_round'),
        'status': session_data['user_attempt'].status.value,
        'time_limit_seconds': 60,
        'time_remaining': time_remaining,
        'questions_unlimited': True,
        'current_streak': session_data['user_attempt'].current_streak,
        'questions_answered': session_data['user_attempt'].questions_answered,
        'correct_answers': session_data['user_attempt'].correct_answers,
        'score_multiplier': 5,  # Points per correct answer
        'question': {
            'id': question.id,
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }
        }
    }


def streak_target_mode(db: Session, current_user: User):
    """Start streak target challenge - maintain 5-question streak"""

    # === Create daily challenge session ===
    session_data = create_challenge_session(db, current_user.id, 'streak_target')

    # === Check if user already completed ===
    if "error" in session_data:
        return session_data

    # === Get first question ===
    question = get_random_question(db)
    if not question:
        raise HTTPException(status_code=404, detail='No questions available')

    return {
        'challenge_id': session_data['daily_challenge'].id,
        'attempt_id': session_data['user_attempt'].id,
        'challenge_type': 'streak_target',
        'challenge_info': get_challenge_info('streak_target'),
        'status': session_data['user_attempt'].status.value,
        'target_streak': 5,
        'current_streak': session_data['user_attempt'].current_streak,
        'max_streak': session_data['user_attempt'].max_streak,
        'progress': f"{session_data['user_attempt'].current_streak}/5",
        'questions_answered': session_data['user_attempt'].questions_answered,
        'correct_answers': session_data['user_attempt'].correct_answers,
        'wrong_answers': session_data['user_attempt'].wrong_answers,
        'streak_broken_count': session_data['user_attempt'].wrong_answers,
        'question': {
            'id': question.id,
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }
        }
    }


def marathon_mode(db: Session, current_user: User):
    """Start marathon mode challenge - complete 25 questions"""

    # === Create daily challenge session ===
    session_data = create_challenge_session(db, current_user.id, 'marathon_mode')

    # === Check if user already completed ===
    if "error" in session_data:
        return session_data

    # === Get first question ===
    question = get_random_question(db)
    if not question:
        raise HTTPException(status_code=404, detail='No questions available')

    return {
        'challenge_id': session_data['daily_challenge'].id,
        'attempt_id': session_data['user_attempt'].id,
        'challenge_type': 'marathon_mode',
        'challenge_info': get_challenge_info('marathon_mode'),
        'status': session_data['user_attempt'].status.value,
        'total_questions': 25,
        'questions_remaining': 25 - session_data['user_attempt'].questions_answered,
        'progress': f"{session_data['user_attempt'].questions_answered}/25",
        'completion_percentage': (session_data['user_attempt'].questions_answered / 25) * 100,
        'current_streak': session_data['user_attempt'].current_streak,
        'max_streak': session_data['user_attempt'].max_streak,
        'questions_answered': session_data['user_attempt'].questions_answered,
        'correct_answers': session_data['user_attempt'].correct_answers,
        'wrong_answers': session_data['user_attempt'].wrong_answers,
        'current_accuracy': session_data['user_attempt'].accuracy_percentage,
        'question': {
            'id': question.id,
            'question_text': question.question_text,
            'options': {
                'A': question.option_a,
                'B': question.option_b,
                'C': question.option_c,
                'D': question.option_d,
            }
        }
    }


def create_challenge_session(db: Session, user_id: int, challenge_type: str):
    """Generic function to create challenge session for any challenge type"""

    # === Get today's challenge or create it ===
    daily_challenge = get_today_challenge(db)
    if not daily_challenge:
        daily_challenge = DailyChallenge(
            challenge_date=date.today(),
            challenge_type=challenge_type,
            is_active=True
        )
        db.add(daily_challenge)
        db.flush()
        db.commit()

    # === Get or create user attempt ===
    user_attempt = get_or_create_user_attempt(db, user_id, daily_challenge.id)

    # === If user already completed today's challenge ===
    if user_attempt.is_completed:
        return {
            'error': f"You have already completed today's {challenge_type} challenge",
            'attempt': user_attempt
        }

    # === Set started_at if not already set ===
    if not user_attempt.started_at and challenge_type != 'lightning_round':
        user_attempt.started_at = datetime.now(timezone.utc)
        db.commit()

    return {
        'daily_challenge': daily_challenge,
        'user_attempt': user_attempt
    }

# ############################ END OTHER MODE ############################

# ########################### ANSWER ############################


# === Challenge-specific handlers ===
def handle_survival_mode_answer(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle survival mode logic - game over after 3 wrong answers"""

    lives_remaining = 3 - attempt.wrong_answers

    # === Check if game over (3 wrong answers) ===
    if attempt.wrong_answers >= 3:
        # === Game over - survival mode failed ===
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = False
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.correct_answers

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": False,
            "lives_remaining": 0,
            "final_stats": {
                "current_streak": attempt.current_streak,
                "max_streak": attempt.max_streak,
                "questions_answered": attempt.questions_answered,
                "correct_answers": attempt.correct_answers,
                "wrong_answers": attempt.wrong_answers,
                "accuracy": attempt.accuracy_percentage,
                "final_score": attempt.final_score
            },
            "message": "Game Over! You got 3 questions wrong."
        }

    # === Continue game - get next question ===
    db.commit()
    next_question = get_random_question(db)

    if not next_question:
        raise HTTPException(status_code=500, detail="No more questions available")

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "game_over": False,
        "challenge_completed": False,
        "lives_remaining": lives_remaining,
        "current_streak": attempt.current_streak,
        "max_streak": attempt.max_streak,
        "questions_answered": attempt.questions_answered,
        "correct_answers": attempt.correct_answers,
        "wrong_answers": attempt.wrong_answers,
        "accuracy": attempt.accuracy_percentage,
        "next_question": {
            "id": next_question.id,
            "question_text": next_question.question_text,
            "options": {
                "A": next_question.option_a,
                "B": next_question.option_b,
                "C": next_question.option_c,
                "D": next_question.option_d
            }
        }
    }


'''
def handle_perfect_score_answer_(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle perfect score logic - 100% accuracy required"""

    # === If any wrong answer, challenge failed ===
    if not is_correct:
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = False
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.correct_answers

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": False,
            "message": "Perfect Score Challenge Failed! You need 100% accuracy.",
            "final_stats": build_final_stats(attempt)
        }

    # === Check if completed 10 questions with perfect score ===
    if attempt.questions_answered >= 10:
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = True
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.correct_answers * 20  # Bonus points for perfect score

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": True,
            "message": "Perfect Score Achieved! 🎉",
            "final_stats": build_final_stats(attempt)
        }

    # === Continue with next question ===
    db.commit()
    next_question = get_random_question(db)

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "game_over": False,
        "challenge_completed": False,
        "questions_remaining": 10 - attempt.questions_answered,
        "progress": f"{attempt.questions_answered}/10",
        "next_question": build_question_response(next_question)
    }
'''


def handle_marathon_mode_answer(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle marathon mode logic - complete 25 questions"""

    # === Check if completed all 25 questions ===
    if attempt.questions_answered >= 25:
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = True
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.correct_answers * 10

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": True,
            "message": f"Marathon Completed! You answered {attempt.correct_answers}/25 correctly.",
            "final_stats": build_final_stats(attempt)
        }

    # === Continue marathon ===
    db.commit()
    next_question = get_random_question(db)

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "game_over": False,
        "challenge_completed": False,
        "questions_remaining": 25 - attempt.questions_answered,
        "progress": f"{attempt.questions_answered}/25",
        "next_question": build_question_response(next_question)
    }


def handle_speed_challenge_answer(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle speed challenge logic - 10 questions in 2 minutes"""

    # === Check time limit (2 minutes = 120 seconds) ===
    time_elapsed = (datetime.now(timezone.utc) - attempt.started_at).total_seconds()

    if time_elapsed > 120:
        # === Time's up! ===
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = False
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.time_taken = time_elapsed
        attempt.final_score = attempt.correct_answers

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": False,
            "message": "Time's Up! You didn't finish in 2 minutes.",
            "time_taken": time_elapsed,
            "final_stats": build_final_stats(attempt)
        }

    # === Check if completed 10 questions ===
    if attempt.questions_answered >= 10:
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = True
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.time_taken = time_elapsed
        attempt.final_score = attempt.correct_answers * 15  # Speed bonus

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": True,
            "message": f"Speed Challenge Completed in {time_elapsed:.1f} seconds! 🚀",
            "time_taken": time_elapsed,
            "final_stats": build_final_stats(attempt)
        }

    # === Continue speed challenge ===
    db.commit()
    next_question = get_random_question(db)

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "game_over": False,
        "challenge_completed": False,
        "questions_remaining": 10 - attempt.questions_answered,
        "time_remaining": max(0, 120 - time_elapsed),
        "progress": f"{attempt.questions_answered}/10",
        "next_question": build_question_response(next_question)
    }


def handle_lightning_round_answer(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle lightning round logic - as many questions as possible in 60 seconds"""

    # === Ensure started_at is set - if not set, set it now (this is the first question) ===
    if not attempt.started_at:
        attempt.started_at = datetime.now(timezone.utc)
        time_elapsed = 0  # First question, no time elapsed yet
        db.commit()  # Save the started_at time immediately
    else:
        time_elapsed = (datetime.now(timezone.utc) - attempt.started_at).total_seconds()

    # === Only check time limit if this is not the first question (time_elapsed > 1) ===
    if time_elapsed > 1 and time_elapsed > 60:
        # === Time's up! ===
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = True  # Always successful if you tried
        attempt.completed_at = datetime.now(timezone.utc)
        print(f'time_taken: {time_elapsed}')
        attempt.time_taken = time_elapsed
        attempt.final_score = attempt.correct_answers * 5

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": True,
            "message": f"Lightning Round Complete! You answered {attempt.questions_answered} questions!",
            "time_taken": time_elapsed,
            "final_stats": build_final_stats(attempt)
        }

    # === Continue lightning round ===
    db.commit()
    next_question = get_random_question(db)

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "game_over": False,
        "challenge_completed": False,
        "time_remaining": max(0, 60 - time_elapsed),
        "questions_answered": attempt.questions_answered,
        "next_question": build_question_response(next_question)
    }


def handle_streak_target_answer(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle streak target logic - maintain 5-question streak"""

    # === Check if achieved 5-question streak ===
    if attempt.current_streak >= 5:
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = True
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.current_streak * 25

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": True,
            "message": "Streak Target Achieved! 5 questions in a row! 🔥",
            "final_stats": build_final_stats(attempt)
        }

    # === Check if streak broken and too many attempts ===
    if not is_correct and attempt.questions_answered > 15:  # Give reasonable attempts
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = False
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.max_streak * 10

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": False,
            "message": "Streak Target Failed! Too many attempts without reaching 5 streak.",
            "final_stats": build_final_stats(attempt)
        }

    # === Continue streak challenge ===
    db.commit()
    next_question = get_random_question(db)     # i already defined it.

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "game_over": False,
        "challenge_completed": False,
        "current_streak": attempt.current_streak,
        "target_streak": 5,
        "progress": f"{attempt.current_streak}/5",
        "next_question": build_question_response(next_question)
    }


# === Helper functions ===
def build_final_stats(attempt: UserChallengeAttempt) -> dict:
    """Build standardized final stats object"""
    return {
        "current_streak": attempt.current_streak,
        "max_streak": attempt.max_streak,
        "questions_answered": attempt.questions_answered,
        "correct_answers": attempt.correct_answers,
        "wrong_answers": attempt.wrong_answers,
        "accuracy": attempt.accuracy_percentage,
        "final_score": attempt.final_score,
        "time_taken": attempt.time_taken
    }


def build_question_response(question: Question) -> dict:
    """Build standardized question response"""
    if not question:
        return None

    return {
        "id": question.id,
        "question_text": question.question_text,
        "options": {
            "A": question.option_a,
            "B": question.option_b,
            "C": question.option_c,
            "D": question.option_d
        }
    }


# === You'll also need to add these placeholder handlers for the remaining challenges: ===
def handle_perfect_score_answer(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle perfect score logic - 100% accuracy on 10 questions"""

    # === If any wrong answer, challenge failed ===
    if not is_correct:
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = False
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.correct_answers

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": False,
            "message": "Perfect Score Challenge Failed! You need 100% accuracy.",
            "final_stats": build_final_stats(attempt)
        }

    # === Check if completed 10 questions with perfect score ===
    if attempt.questions_answered >= 10:
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = True
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.final_score = attempt.correct_answers * 20  # Perfect score bonus

        db.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "game_over": True,
            "challenge_completed": True,
            "challenge_successful": True,
            "message": "Perfect Score Achieved! 🎉",
            "final_stats": build_final_stats(attempt)
        }

    # === Continue with next question ===
    db.commit()
    next_question = get_random_question(db)

    return {
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "game_over": False,
        "challenge_completed": False,
        "questions_remaining": 10 - attempt.questions_answered,
        "progress": f"{attempt.questions_answered}/10",
        "next_question": build_question_response(next_question)
    }


# ############################ END ANSWER ############################

def run_functions(challenge_type: str, db: Session, current_user: User):
    match (challenge_type):
        # case 'speed_challenge' | 'perfect_score' | 'lightning_round' | 'streak_target' | 'marathon_mode':
        case 'survival_mode':
            return survival_mode(db, current_user)

        case 'perfect_score':
            return perfect_score_mode(db, current_user)

        case 'speed_challenge':
            return speed_challenge_mode(db, current_user)

        case 'lightning_round':
            return lightning_round_mode(db, current_user)

        case 'streak_target':
            return streak_target_mode(db, current_user)

        case 'marathon_mode':
            return marathon_mode(db, current_user)

        case _:
            raise ValueError(f'Unknown challenge: {challenge_type}')


@router.post('/start/daily-challenge')
def daily_challenge(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Start today daily challenge"""

    # === Get today challenge ===
    todays_challenge = get_today_challenge_type()
    # todays_challenge = 'survival_mode'
    print(f'\n\ntodays_challenge: {todays_challenge}')

    # === Get challenge details ===
    challenge_info = get_challenge_info(todays_challenge)
    print(f'challenge_info: {challenge_info}')

    # === Get Today challenge ===
    daily_schedule = get_daily_schedule()
    print(f'\nDaily Schedule: {daily_schedule}')

    return run_functions(todays_challenge, db, current_user)


@router.post('/start/daily-challenge-answer')
def daily_challenge_answer(request: AnswerSubmissionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Dynamic answer submission handler for all challenge types"""

    # === 1. Get and validate user attempt ===
    attempt = db.query(UserChallengeAttempt).filter(
        UserChallengeAttempt.id == request.attempt_id,
        UserChallengeAttempt.user_id == current_user.id
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Challenge attempt not found")

    if attempt.is_completed:
        raise HTTPException(status_code=400, detail="Challenge already completed")

    # === 2. Get question and validate answer ===
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = question.correct_answer.upper() == request.selected_answer.upper()

    # === 3. Update attempt stats (common for all challenges) ===
    attempt.questions_answered += 1
    if is_correct:
        attempt.correct_answers += 1
        attempt.current_streak += 1
        if attempt.current_streak > attempt.max_streak:
            attempt.max_streak = attempt.current_streak
    else:
        attempt.wrong_answers += 1
        attempt.current_streak = 0

    # === Get challenge type first ===
    challenge_type = attempt.daily_challenge.challenge_type

    # === Update status to in_progress if first question ===
    if attempt.status == ChallengeStatus.NOT_STARTED:
        attempt.status = ChallengeStatus.IN_PROGRESS
        # For lightning round, start timer now when first answer is submitted
        if challenge_type == 'lightning_round' and not attempt.started_at:
            attempt.started_at = datetime.now(timezone.utc)

    # === Calculate accuracy ===
    if attempt.questions_answered > 0:
        attempt.accuracy_percentage = (attempt.correct_answers / attempt.questions_answered) * 100

    attempt.updated_at = datetime.now(timezone.utc)

    # === 4. Get challenge type and route to specific logic ===
    challenge_type = attempt.daily_challenge.challenge_type

    match challenge_type:
        case 'survival_mode':
            return handle_survival_mode_answer(db, attempt, question, is_correct)

        case 'perfect_score':
            return handle_perfect_score_answer(db, attempt, question, is_correct)

        case 'speed_challenge':
            return handle_speed_challenge_answer(db, attempt, question, is_correct)

        case 'lightning_round':
            return handle_lightning_round_answer(db, attempt, question, is_correct)

        case 'streak_target':
            return handle_streak_target_answer(db, attempt, question, is_correct)

        case 'marathon_mode':
            return handle_marathon_mode_answer(db, attempt, question, is_correct)

        case _:
            raise HTTPException(status_code=400, detail=f"Unknown challenge type: {challenge_type}")


@router.get('/daily-challenge/progress')
def get_daily_challenge_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's progress on today's daily challenge"""

    # === Get today's challenge ===
    daily_challenge = get_today_challenge(db)  # Fixed function name

    if not daily_challenge:
        todays_challenge_type = get_today_challenge_type()  # Fixed function name
        return {
            "challenge_available": True,
            "challenge_type": todays_challenge_type,
            "challenge_info": get_challenge_info(todays_challenge_type),
            "has_attempted": False,
            "message": "Daily challenge available - not started yet"
        }

    # === Get user's attempt ===
    attempt = db.query(UserChallengeAttempt).filter(
        UserChallengeAttempt.user_id == current_user.id,
        UserChallengeAttempt.daily_challenge_id == daily_challenge.id
    ).first()

    if not attempt:
        return {
            "challenge_available": True,
            "challenge_type": daily_challenge.challenge_type,
            "challenge_info": get_challenge_info(daily_challenge.challenge_type),
            "has_attempted": False,
            "message": "Daily challenge available - not started yet"
        }

    # === Build challenge-specific progress data ===
    challenge_progress = get_challenge_progress_data(daily_challenge.challenge_type, attempt)

    return {
        "challenge_available": True,
        "challenge_type": daily_challenge.challenge_type,
        "challenge_info": get_challenge_info(daily_challenge.challenge_type),
        "has_attempted": True,
        "status": attempt.status.value,
        "current_streak": attempt.current_streak,
        "max_streak": attempt.max_streak,
        "questions_answered": attempt.questions_answered,
        "correct_answers": attempt.correct_answers,
        "wrong_answers": attempt.wrong_answers,
        "accuracy": attempt.accuracy_percentage,
        "is_completed": attempt.is_completed,
        "is_successful": attempt.is_successful,
        "final_score": attempt.final_score,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        **challenge_progress  # Merge challenge-specific data
    }


def get_challenge_progress_data(challenge_type: str, attempt: UserChallengeAttempt) -> dict:
    """Get challenge-specific progress data"""
    match challenge_type:
        case 'survival_mode':
            return {"lives_remaining": 3 - attempt.wrong_answers}
        case 'marathon_mode':
            return {"questions_remaining": 25 - attempt.questions_answered}
        case 'perfect_score':
            return {
                "questions_remaining": 10 - attempt.questions_answered,
                "perfect_streak": attempt.wrong_answers == 0
            }
        case 'speed_challenge':
            return {"questions_remaining": 10 - attempt.questions_answered}
        case _:
            return {}


@router.get('/today-challenge')
def get_today_challenge_info(db: Session = Depends(get_db)):
    """Get information about today's challenge"""

    # === Get today's challenge type ===
    todays_challenge_type = get_today_challenge_type()  # Fixed function name

    # === Get challenge details ===
    challenge_info = get_challenge_info(todays_challenge_type)

    # === Get daily schedule ===
    daily_schedule = get_daily_schedule()

    # === Check if challenge already exists in database ===
    existing_challenge = get_today_challenge(db)

    return {
        "today_challenge": todays_challenge_type,
        "challenge_info": challenge_info,
        "daily_schedule": daily_schedule,
        "challenge_created": existing_challenge is not None,
        "challenge_date": existing_challenge.challenge_date.strftime('%Y-%m-%d') if existing_challenge else None
    }
