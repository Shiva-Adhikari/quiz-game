# Standard library imports
from datetime import datetime, timedelta, timezone

# Third-party imports
# from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

# Local imports
from src.utils.db import get_db
from src.utils.enums import SessionStatus
from src.models.questions import Question
from src.models.authentication import User
from src.models.user_profile import UserProfile
from src.utils.quiz import check_and_expire_sessions
from src.utils.level_system import get_level_from_xp
from src.utils.rewards import calculate_quiz_rewards
from src.utils.get_current_user import get_current_user
from src.models.quiz_session import QuizSession, QuizSessionQuestion, UserAnswer
from src.schemas.quiz_session import StartQuizRequest, QuestionResponse, SubmitAnswerRequest, SubmitAnswerResponse, QuizProgressResponse

router = APIRouter(prefix='/RandomQuiz', tags=['RandomQuiz'])


@router.post('/start/random-quiz')
def random_quiz(request: StartQuizRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ Start a new quiz session with 10 random questions
    """

    '''
    active_session = db.query(QuizSession).filter(
        QuizSession.user_id == current_user.id,
        QuizSession.is_active,
        QuizSession.status.in_([SessionStatus.STARTED, SessionStatus.IN_PROGRESS])
    ).first()

    if active_session:
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "You have an active quiz session",
                "active_session_id": active_session.id,
                "session_type": active_session.session_type,
                "questions_answered": active_session.questions_answered,
                "total_questions": active_session.total_questions
            }
        )
    '''

    check_and_expire_sessions(current_user.id, db)

    # get random question
    random_questions = get_random_questions_optimized(db, request.total_questions)

    ''' # for increase performance in large dataset this is better way than top 2 variables (query, random_questions)
    # Step 1: Count total questions
    total_count = session.query(Question).count()  # e.g., 1000 questions

    # Step 2: Calculate random starting point
    request.total_questions = 10  # Want 10 questions
    random_offset = random.randint(0, max(0, 1000 - 10))  # Random number 0-990

    # Step 3: Skip to random position and take 10
    questions = session.query(Question).offset(random_offset).limit(10).all()

    # # OR BOTH IS SAME
    # questions = session.query(Question)\
        # .offset(random_offset)\    # Skip first 'random_offset' rows
        # .limit(10)\               # Take next 10 rows
        # .all()
    '''

    '''
    if len(random_questions) < request.total_questions:
        raise HTTPException(status_code=400, detail=f'Not enough questions available, Found {len(random_questions)}, need {request.total_questions}')
    '''

    # ''' # Calculate timer expiry if time limit is set
    timer_expires_at = None
    if request.time_limit_minutes:
        timer_expires_at = datetime.now(timezone.utc) + timedelta(minutes=request.time_limit_minutes)
    # '''

    # create quiz session
    quiz_session = QuizSession(
        user_id=current_user.id,
        # category_id=request.category_id,
        category_id=None,
        # session_type=SessionType(request.session_type),
        session_type='random',
        difficulty_level='easy',
        total_questions=request.total_questions,
        current_question_index=0,
        questions_answered=0,
        correct_answers=0,
        status=SessionStatus.STARTED,
        is_active=True,
        started_at=datetime.now(timezone.utc),
        last_activity_at=datetime.now(timezone.utc),
        timer_expires_at=None,
        total_time_seconds=0,
        xp_earned=0,
        coins_earned=0
    )

    db.add(quiz_session)
    db.flush()  # get quiz_session.id

    session_questions = [
        QuizSessionQuestion(
            quiz_session_id=quiz_session.id,
            question_id=question.id,
            question_order=idx,
            is_answered=False
        ) for idx, question in enumerate(random_questions, 1)
    ]

    db.add_all(session_questions)
    db.commit()

    questions_response = [
        QuestionResponse(
            question_id=question.id,  # Use the original question object
            question_order=idx,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d
        ) for idx, question in enumerate(random_questions, 1)  # Use random_questions instead
    ]

    return {
        "quiz_session_id": quiz_session.id,
        "session_status": quiz_session.status.value,
        "total_questions": quiz_session.total_questions,
        "current_question": 0,
        "questions": questions_response,
        "timer_expires_at": timer_expires_at,
        "message": f"Quiz started successfully! You have {request.total_questions} questions to answer."
    }


@router.post('/start/random-quiz-answer', response_model=SubmitAnswerResponse)
def submit_answer(request: SubmitAnswerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ Submit answer for a question and get immediate feedback
    """

    # Validate quiz session exists and belongs to current user
    quiz_session = db.query(QuizSession).filter(
        QuizSession.id == request.quiz_session_id,
        QuizSession.user_id == current_user.id,
        QuizSession.is_active
    ).first()

    user_profile = db.query(UserProfile).filter(
        UserProfile.id == current_user.id
    ).first()

    if not user_profile:
        raise HTTPException(status_code=404, detail='User Profile not found')

    if not quiz_session:
        raise HTTPException(status_code=404, detail='Quiz session not found or not active')

    # Check if session is expired
    if quiz_session.timer_expires_at and datetime.now(timezone.utc) > quiz_session.timer_expires_at:
        quiz_session.status = SessionStatus.EXPIRED
        quiz_session.is_active = False
        db.commit()
        raise HTTPException(status_code=400, detail='Quiz session has expired')

    # Validate question belongs to this session
    session_question = db.query(QuizSessionQuestion).filter(
        QuizSessionQuestion.quiz_session_id == request.quiz_session_id,
        QuizSessionQuestion.question_id == request.question_id
    ).first()

    if not session_question:
        raise HTTPException(status_code=400, detail='Question does not belong to this quiz session')

    # Check if question already answered
    existing_answer = db.query(UserAnswer).filter(
        UserAnswer.quiz_session_id == request.quiz_session_id,
        UserAnswer.question_id == request.question_id
    ).first()

    if existing_answer:
        raise HTTPException(status_code=400, detail='Question already answered')

    # Get the actual question to validate answer
    question = db.query(Question).filter(Question.id == request.question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail='Question not found')

    # Validate user answer format
    user_answer = request.user_answer.upper()
    if user_answer not in ['A', 'B', 'C', 'D']:
        raise HTTPException(status_code=400, detail='Invalid answer format, Must be A, B, C, or D')

    # Check if answer is correct
    is_correct = user_answer == question.correct_answer.upper()

    # Calculate time taken (you might want to track question start time)
    time_taken = 30  # Default, you can implement proper timing

    # Record the answer
    user_answer_record = UserAnswer(
        quiz_session_id=request.quiz_session_id,
        question_id=request.question_id,
        user_answer=user_answer,
        is_correct=is_correct,
        time_taken_seconds=time_taken,
        answered_at=datetime.now(timezone.utc)
    )
    db.add(user_answer_record)

    # Update session progress
    quiz_session.questions_answered += 1
    quiz_session.last_activity_at = datetime.now(timezone.utc)

    if is_correct:
        quiz_session.correct_answers += 1

    # Mark session question as answered
    session_question.is_answered = True

    # Check if quiz is completed
    session_completed = quiz_session.questions_answered >= quiz_session.total_questions
    next_question_order = None

    if session_completed:
        quiz_session.status = SessionStatus.COMPLETED
        quiz_session.is_active = False
        quiz_session.completed_at = datetime.now(timezone.utc)

        # Calculate rewards (XP, coins)
        rewards = calculate_quiz_rewards(
            correct_answers=quiz_session.correct_answers,
            total_questions=quiz_session.total_questions,
            difficulty_level="mixed",
            session_type="random"
        )

        quiz_session.xp_earned = rewards["xp_earned"]
        quiz_session.coins_earned = rewards["coins_earned"]
        
        user_profile.coins += quiz_session.coins_earned  
        user_profile.total_xp += quiz_session.xp_earned
        user_profile.total_games_played += 1

        level_info = get_level_from_xp(db, user_profile.total_xp)
        user_profile.current_level = level_info["level"]
    else:
        quiz_session.status = SessionStatus.IN_PROGRESS
        # Get next question order
        next_question_order = quiz_session.questions_answered + 1

    db.commit()

    # Calculate score percentage
    score_percentage = (quiz_session.correct_answers / quiz_session.questions_answered) * 100

    # Prepare response
    message = "Correct! ✅" if is_correct else "Incorrect! ❌"
    if session_completed:
        message += f'Quiz completed! Final score: {quiz_session.correct_answers}/{quiz_session.total_questions}'

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        # explanation=question.explanation,
        current_score=quiz_session.correct_answers,
        questions_answered=quiz_session.questions_answered,
        total_questions=quiz_session.total_questions,
        score_percentage=round(score_percentage, 2),
        session_completed=session_completed,
        next_question_order=next_question_order,
        message=message
    )


@router.get('/start/progress/{quiz_session_id}', response_model=QuizProgressResponse)
def get_quiz_progress(quiz_session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """ get current progress of quiz session
    """

    quiz_session = db.query(QuizSession).filter(
        QuizSession.id == quiz_session_id,
        QuizSession.user_id == current_user.id
    ).first()

    if not quiz_session:
        raise HTTPException(status_code=404, detail='Quiz session not found')

    # Calculate time remaining
    time_remaining_seconds = None
    if quiz_session.timer_expires_at:
        remaining = quiz_session.timer_expires_at - datetime.now(timezone.utc)
        time_remaining_seconds = max(0, int(remaining.total_seconds()))

    score_percentage = 0
    if quiz_session.questions_answered > 0:
        score_percentage = (quiz_session.correct_answers / quiz_session.questions_answered) * 100

    return QuizProgressResponse(
        quiz_session_id=quiz_session.id,
        status=quiz_session.status.value,
        current_question=quiz_session.current_question_index,
        questions_answered=quiz_session.questions_answered,
        total_questions=quiz_session.total_questions,
        correct_answers=quiz_session.correct_answers,
        score_percentage=round(score_percentage, 2),
        time_remaining_seconds=time_remaining_seconds,
        is_completed=quiz_session.status == SessionStatus.COMPLETED
    )


@router.get('/quiz/results/{quiz_session_id}')
def get_quiz_results(quiz_session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """ Get detailed results after quiz completion
    """

    quiz_session = db.query(QuizSession).filter(
        QuizSession.id == quiz_session_id,
        QuizSession.user_id == current_user.id,
        QuizSession.status == SessionStatus.COMPLETED
    ).first()

    if not quiz_session:
        raise HTTPException(status_code=404, detail='Completed quiz session not found')

    # Get all answers with question details
    answers = db.query(UserAnswer).join(Question).filter(
        UserAnswer.quiz_session_id == quiz_session_id
    ).all()

    answers_breakdown = [
        {
            'question_id': answer.question_id,
            # 'question_text': answer.question_text,
            'user_answer': answer.user_answer,
            'correct_answer': answer.user_answer,
            'is_correct': answer.is_correct,
            'time_taken_seconds': answer.time_taken_seconds
        } for answer in answers
    ]

    total_time = None
    if quiz_session.completed_at and quiz_session.started_at:
        total_time = quiz_session.completed_at - quiz_session.started_at

    return {
        'quiz_session_id': quiz_session.id,
        'final_score': quiz_session.correct_answers,
        'total_questions': quiz_session.total_questions,
        'score_percentage': round((quiz_session.correct_answers / quiz_session.total_questions) * 100, 2),
        'xp_earned': quiz_session.xp_earned,
        'coins_earned': quiz_session.coins_earned,
        'total_time': str(total_time) if total_time else None,
        'difficulty_level': quiz_session.category_id,
        'answers_breakdown': answers_breakdown
    }


@router.delete("/quiz/abandon/{quiz_session_id}")
def abandon_quiz(
    quiz_session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Abandon an active quiz session
    """
    quiz_session = db.query(QuizSession).filter(
        QuizSession.id == quiz_session_id,
        QuizSession.user_id == current_user.id,
        QuizSession.is_active
    ).first()

    if not quiz_session:
        raise HTTPException(status_code=404, detail="Active quiz session not found")

    quiz_session.status = SessionStatus.ABANDONED
    quiz_session.is_active = False
    quiz_session.completed_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Quiz session abandoned successfully"}


@router.get("/quiz/active")
def get_active_quiz(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Get user's current active quiz session if any
    """

    active_session = db.query(QuizSession).filter(
        QuizSession.user_id == current_user.id,
        QuizSession.is_active
    ).first()

    if not active_session:
        return {"message": "No active quiz session found", "active_session": None}

    return {
        "message": "Active quiz session found",
        "active_session": {
            "quiz_session_id": active_session.id,
            "status": active_session.status.value,
            "questions_answered": active_session.questions_answered,
            "total_questions": active_session.total_questions,
            "current_score": active_session.correct_answers
        }
    }


def get_random_questions_optimized(db: Session, limit: int):
    """Optimized random question selection"""
    # Count total active questions
    total_count = db.query(Question).filter(Question.is_active).count()
    
    if total_count < limit:
        # Return all available if not enough questions
        return db.query(Question).filter(Question.is_active).all()
    
    # Generate random offsets
    import random
    offsets = set()
    while len(offsets) < limit:
        offsets.add(random.randint(0, total_count - 1))
    
    # Get questions at random positions
    questions = []
    for offset in offsets:
        question = db.query(Question).filter(Question.is_active).offset(offset).first()
        if question:
            questions.append(question)
    
    return questions
