# Standard library imports
# import uuid
from datetime import (
    datetime, timedelta,
    # timezone
)

# Third-party imports
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import (
    APIRouter, Depends,
    # HTTPException,
    # Response,
    # Request
)

# Local imports
from src.utils.db import get_db
from src.utils.get_current_user import get_current_user
from src.models.authentication import (
    User,
)
# from src.models.user_data import QuizSession
from src.models.questions import Question
from src.utils.enums import (
    # SessionType, DifficultyLevel,
    SessionStatus
)
from src.models.quiz_session import (
    QuizSession, QuizSessionQuestion,
    # UserAnswer
)
from src.schemas.quiz_session import (
    StartQuizRequest, QuestionResponse,
    # StartQuizResponse,
    SubmitAnswerRequest,
    # SubmitAnswerResponse, QuizProgressResponse
)

router = APIRouter(prefix='/StartQuiz', tags=['StartQuiz'])


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
        raise HTTPException(status_code=400, detail=f'You already have an active quiz session (ID: {active_session.id}). Complete it first.')
    '''

    # get random question
    query = db.query(Question).filter(Question.is_active)

    random_questions = query.order_by(func.random()).limit(request.total_questions).all()

    '''
    if len(random_questions) < request.total_questions:
        raise HTTPException(status_code=400, detail=f'Not enough questions available, Found {len(random_questions)}, need {request.total_questions}')
    '''

    # ''' # Calculate timer expiry if time limit is set
    timer_expires_at = None
    if request.time_limit_minutes:
        timer_expires_at = datetime.utcnow() + timedelta(minutes=request.time_limit_minutes)
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
        started_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
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
