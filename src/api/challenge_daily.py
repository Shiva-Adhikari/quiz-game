from datetime import date, datetime
import hashlib
import random
from src.models.questions import Question
from src.utils.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException
from src.utils.get_current_user import get_current_user
from src.models.authentication import User
from src.models.challenge_daily import DailyChallenge, UserChallengeAttempt, ChallengeStatus
from src.schemas.challenge_daily import AnswerSubmissionRequest


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

    # Reset random seed
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
    # challenge = get_today_challenge_type()
    challenge = 'survival_mode'
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
            started_at=datetime.utcnow()
        )
        db.add(attempt)
        db.flush()
        db.commit()

    return attempt


def create_survival_mode_session(db: Session, user_id: int):
    """Create a new survival mode daily challenge session"""

    # Get today's challenge or create it
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

    # Get or create user attempt
    user_attempt = get_or_create_user_attempt(db, user_id, daily_challenge.id)

    # If user already completed today's challenge
    if user_attempt.is_completed:
        return {
            'error': "You have already completed today's daily challenge",
            'attempt': user_attempt
        }

    # ADD THIS RETURN STATEMENT:
    return {
        'daily_challenge': daily_challenge,
        'user_attempt': user_attempt
    }


def survival_mode(db: Session, current_user: User):
    """Get survival mode challenge"""

    # Create daily challenge session
    session_data = create_survival_mode_session(db, current_user.id)

    # Check if user already completed
    if "error" in session_data:
        return session_data

    # Get first question
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


# ########################### ANSWER ############################

# Challenge-specific handlers
def handle_survival_mode(db: Session, attempt: UserChallengeAttempt, question: Question, is_correct: bool):
    """Handle survival mode logic - game over after 3 wrong answers"""

    lives_remaining = 3 - attempt.wrong_answers

    # Check if game over (3 wrong answers)
    if attempt.wrong_answers >= 3:
        # Game over - survival mode failed
        attempt.status = ChallengeStatus.COMPLETED
        attempt.is_completed = True
        attempt.is_successful = False
        attempt.completed_at = datetime.utcnow()
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

    # Continue game - get next question
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


# ############################ END ANSWER ############################

def run_functions(challenge_type: str, db: Session, current_user: User):
    match (challenge_type):
        # case 'speed_challenge' | 'perfect_score' | 'lightning_round' | 'streak_target' | 'marathon_mode':
        case 'survival_mode':
            return survival_mode(db, current_user)

        case 'perfect_score':
            pass

        case 'speed_challenge':
            pass

        case 'lightning_round':
            pass

        case 'streak_target':
            pass

        case 'marathon_mode':
            pass

        case _:
            raise ValueError(f'Unknown challenge: {challenge_type}')


@router.post('/start/daily-challenge')
def daily_challenge(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Start today daily challenge"""

    # Get today challenge
    # todays_challenge = get_today_challenge_type()
    todays_challenge = 'survival_mode'
    print(f'\n\ntodays_challenge: {todays_challenge}')

    # Get challenge details
    challenge_info = get_challenge_info(todays_challenge)
    print(f'challenge_info: {challenge_info}')

    # Get Today challenge
    daily_schedule = get_daily_schedule()
    print(f'\nDaily Schedule: {daily_schedule}')

    return run_functions(todays_challenge, db, current_user)


@router.post('/start/daily-challenge-answer')
def daily_challenge_answer(request: AnswerSubmissionRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Dynamic answer submission handler for all challenge types"""

    # 1. Get and validate user attempt
    attempt = db.query(UserChallengeAttempt).filter(
        UserChallengeAttempt.id == request.attempt_id,
        UserChallengeAttempt.user_id == current_user.id
    ).first()

    if not attempt:
        raise HTTPException(status_code=404, detail="Challenge attempt not found")

    if attempt.is_completed:
        raise HTTPException(status_code=400, detail="Challenge already completed")

    # 2. Get question and validate answer
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = question.correct_answer.upper() == request.selected_answer.upper()

    # 3. Update attempt stats (common for all challenges)
    attempt.questions_answered += 1
    if is_correct:
        attempt.correct_answers += 1
        attempt.current_streak += 1
        if attempt.current_streak > attempt.max_streak:
            attempt.max_streak = attempt.current_streak
    else:
        attempt.wrong_answers += 1
        attempt.current_streak = 0

    # Update status to in_progress if first question
    if attempt.status == ChallengeStatus.NOT_STARTED:
        attempt.status = ChallengeStatus.IN_PROGRESS

    # Calculate accuracy
    if attempt.questions_answered > 0:
        attempt.accuracy_percentage = (attempt.correct_answers / attempt.questions_answered) * 100

    attempt.updated_at = datetime.utcnow()

    # 4. Get challenge type and route to specific logic
    challenge_type = attempt.daily_challenge.challenge_type

    match challenge_type:
        case 'survival_mode':
            return handle_survival_mode(db, attempt, question, is_correct)

        case 'perfect_score':
            # return handle_perfect_score(db, attempt, question, is_correct)
            pass

        case 'speed_challenge':
            # return handle_speed_challenge(db, attempt, question, is_correct)
            pass

        case 'lightning_round':
            # return handle_lightning_round(db, attempt, question, is_correct)
            pass

        case 'streak_target':
            # return handle_streak_target(db, attempt, question, is_correct)
            pass

        case 'marathon_mode':
            # return handle_marathon_mode(db, attempt, question, is_correct)
            pass

        case _:
            raise HTTPException(status_code=400, detail=f"Unknown challenge type: {challenge_type}")
