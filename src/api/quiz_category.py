# Standard library imports
from datetime import datetime, timedelta, timezone

# Third-party imports
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

# Local imports
from src.utils.db import get_db
from src.utils.enums import SessionStatus
from src.models.authentication import User
from src.models.user_profile import UserProfile
from src.models.questions import Question, Category
from src.utils.quiz import check_and_expire_sessions
from src.utils.rewards import calculate_quiz_rewards
from src.utils.level_system import get_level_from_xp
from src.utils.get_current_user import get_current_user
from src.models.quiz_session import QuizSession, QuizSessionQuestion, UserAnswer
from src.schemas.quiz_session import StartCategoryQuizRequest, QuestionResponse, SubmitAnswerRequest, SubmitAnswerResponse, QuizProgressResponse

router = APIRouter(prefix='/CategoryQuiz', tags=['CategoryQuiz'])


@router.get('/categories')
def get_available_categories(db: Session = Depends(get_db)):
    """Get all available categories for quiz"""

    categories = db.query(Category).filter(Category.is_active).all()

    if not categories:
        raise HTTPException(status_code=404, detail='No categories available')

    category_list = []
    for category in categories:
        # Count available questions in each category
        question_count = db.query(Question).filter(
            Question.category_id == category.id,
            Question.is_active
        ).count()

        category_list.append({
            "category_id": category.id,
            "category_name": category.name,
            "description": category.description,
            "available_questions": question_count
        })

    return {
        "categories": category_list,
        "message": "Available categories retrieved successfully"
    }


@router.post('/start/category-quiz')
def start_category_quiz(request: StartCategoryQuizRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Start a new quiz session with questions from a specific category"""

    # active_session = db.query(QuizSession).filter(
    #     QuizSession.user_id == current_user.id,
    #     QuizSession.is_active,
    #     QuizSession.status.in_([SessionStatus.STARTED, SessionStatus.IN_PROGRESS])
    # ).first()

    # if active_session:
    #     raise HTTPException(
    #         status_code=400,
    #         detail={
    #             "message": "You have an active quiz session",
    #             "active_session_id": active_session.id,
    #             "session_type": active_session.session_type,
    #             "questions_answered": active_session.questions_answered,
    #             "total_questions": active_session.total_questions
    #         }
    #     )

    check_and_expire_sessions(current_user.id, db)

    # Validate category exists and is active
    category = db.query(Category).filter(
        Category.id == request.category_id,
        Category.is_active
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail='Category not found or inactive')

    filters = [
        Question.category_id == request.category_id,
        Question.is_active
    ]

    if hasattr(request, 'difficulty_level') and request.difficulty_level:
        filters.append(Question.difficulty_level == request.difficulty_level)

    # Count available questions first
    available_count = db.query(Question).filter(*filters).count()

    if available_count < request.total_questions:
        # Use all available questions if not enough
        category_questions = db.query(Question).filter(*filters).all()
    else:
        # Use subquery for better performance
        subquery = db.query(Question.id).filter(*filters).subquery()
        category_questions = (
            db.query(Question)
            .join(subquery, Question.id == subquery.c.id)
            .order_by(func.random())
            .limit(request.total_questions)
            .all()
        )

    '''
    if len(category_questions) < request.total_questions:
        raise HTTPException(
            status_code=400,
            detail=f'Not enough questions available in this category. Found {len(category_questions)}, need {request.total_questions}'
        )
    '''

    # Calculate timer expiry if time limit is set
    timer_expires_at = None
    if request.time_limit_minutes:
        timer_expires_at = datetime.now(timezone.utc) + timedelta(minutes=request.time_limit_minutes)

    # Create quiz session
    quiz_session = QuizSession(
        user_id=current_user.id,
        category_id=request.category_id,
        session_type='category',
        difficulty_level=getattr(request, 'difficulty_level', 'mixed'),
        total_questions=request.total_questions,
        current_question_index=0,
        questions_answered=0,
        correct_answers=0,
        status=SessionStatus.STARTED,
        is_active=True,
        started_at=datetime.now(timezone.utc),
        last_activity_at=datetime.now(timezone.utc),
        timer_expires_at=timer_expires_at,
        total_time_seconds=0,
        xp_earned=0,
        coins_earned=0
    )

    db.add(quiz_session)
    db.flush()  # Get quiz_session.id

    # Create session questions
    session_questions = [
        QuizSessionQuestion(
            quiz_session_id=quiz_session.id,
            question_id=question.id,
            question_order=idx,
            is_answered=False
        ) for idx, question in enumerate(category_questions, 1)
    ]

    db.add_all(session_questions)
    db.commit()

    # Prepare questions response
    questions_response = [
        QuestionResponse(
            question_id=question.id,
            question_order=idx,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            difficulty_level=question.difficulty_level
        ) for idx, question in enumerate(category_questions, 1)
    ]

    return {
        "quiz_session_id": quiz_session.id,
        "category_name": category.name,
        "category_id": category.id,
        "session_status": quiz_session.status.value,
        "total_questions": quiz_session.total_questions,
        "current_question": 0,
        "difficulty_level": quiz_session.difficulty_level,
        "questions": questions_response,
        "timer_expires_at": timer_expires_at,
        # "message": ""
        "message": f"Category quiz started successfully! You have {request.total_questions} questions from '{category.name}' category."
    }


@router.post('/submit-answer', response_model=SubmitAnswerResponse)
def submit_category_quiz_answer(request: SubmitAnswerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Submit answer for a category quiz question and get immediate feedback"""

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
        raise HTTPException(status_code=400, detail='Invalid answer format. Must be A, B, C, or D')

    # Check if answer is correct
    is_correct = user_answer == question.correct_answer.upper()

    # Calculate time taken (implement proper timing based on your needs)
    time_taken = getattr(request, 'time_taken_seconds', 30)

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

        # ''' FIX IT later, make it more simplified
        # Calculate total time
        if quiz_session.started_at:
            # total_time = quiz_session.completed_at - quiz_session.started_at
                    # Convert both to UTC
            started_at_utc = quiz_session.started_at.replace(tzinfo=timezone.utc) if quiz_session.started_at.tzinfo is None else quiz_session.started_at.astimezone(timezone.utc)
            completed_at_utc = quiz_session.completed_at.astimezone(timezone.utc)
            total_time = completed_at_utc - started_at_utc

            quiz_session.total_time_seconds = int(total_time.total_seconds())
        # '''

        # Calculate Rewards
        rewards = calculate_quiz_rewards(
            correct_answers=quiz_session.correct_answers,
            total_questions=quiz_session.total_questions,
            difficulty_level=quiz_session.difficulty_level,
            session_type="category"
        )

        quiz_session.xp_earned = rewards["xp_earned"]
        quiz_session.coins_earned = rewards["coins_earned"]

        user_profile.coins += quiz_session.coins_earned
        user_profile.total_xp += quiz_session.xp_earned
        user_profile.total_games_played += 1

        # Get proper level from level system
        level_info = get_level_from_xp(db, user_profile.total_xp)
        user_profile.current_level = level_info["level"]
    else:
        quiz_session.status = SessionStatus.IN_PROGRESS
        next_question_order = quiz_session.questions_answered + 1

    db.commit()

    # Calculate current score percentage
    score_percentage = (quiz_session.correct_answers / quiz_session.questions_answered) * 100

    # Prepare response message
    message = "Correct! ✅" if is_correct else "Incorrect! ❌"
    if session_completed:
        message += f' Quiz completed! Final score: {quiz_session.correct_answers}/{quiz_session.total_questions}'

    return SubmitAnswerResponse(
        is_correct=is_correct,
        correct_answer=question.correct_answer,
        explanation=getattr(question, 'explanation', None),
        current_score=quiz_session.correct_answers,
        questions_answered=quiz_session.questions_answered,
        total_questions=quiz_session.total_questions,
        score_percentage=round(score_percentage, 2),
        session_completed=session_completed,
        next_question_order=next_question_order,
        xp_earned=quiz_session.xp_earned if session_completed else 0,
        coins_earned=quiz_session.coins_earned if session_completed else 0,
        message=message
    )


@router.get('/progress/{quiz_session_id}', response_model=QuizProgressResponse)
def get_category_quiz_progress(quiz_session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get current progress of category quiz session"""

    quiz_session = db.query(QuizSession).filter(
        QuizSession.id == quiz_session_id,
        QuizSession.user_id == current_user.id
    ).first()

    if not quiz_session:
        raise HTTPException(status_code=404, detail='Quiz session not found')

    # Get category information
    category = db.query(Category).filter(Category.id == quiz_session.category_id).first()

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
        category_id=quiz_session.category_id,
        category_name=category.name if category else "Unknown",
        status=quiz_session.status.value,
        current_question=quiz_session.current_question_index,
        questions_answered=quiz_session.questions_answered,
        total_questions=quiz_session.total_questions,
        correct_answers=quiz_session.correct_answers,
        score_percentage=round(score_percentage, 2),
        difficulty_level=quiz_session.difficulty_level,
        time_remaining_seconds=time_remaining_seconds,
        is_completed=quiz_session.status == SessionStatus.COMPLETED
    )


@router.get('/results/{quiz_session_id}')
def get_category_quiz_results(quiz_session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get detailed results after category quiz completion"""

    quiz_session = db.query(QuizSession).filter(
        QuizSession.id == quiz_session_id,
        QuizSession.user_id == current_user.id,
        QuizSession.status == SessionStatus.COMPLETED
    ).first()

    if not quiz_session:
        raise HTTPException(status_code=404, detail='Completed quiz session not found')

    # Get category information
    category = db.query(Category).filter(Category.id == quiz_session.category_id).first()

    # Get all answers with question details
    answers = db.query(UserAnswer, Question).join(Question).filter(
        UserAnswer.quiz_session_id == quiz_session_id
    ).all()

    answers_breakdown = []
    for answer, question in answers:
        answers_breakdown.append({
            'question_id': answer.question_id,
            'question_text': question.question_text,
            'user_answer': answer.user_answer.lower(),
            'correct_answer': question.correct_answer,
            'is_correct': answer.is_correct,
            'time_taken_seconds': answer.time_taken_seconds,
            'difficulty_level': question.difficulty_level,
            'explanation': getattr(question, 'explanation', None),
            # ✅ ADDED: These fields allow frontend to show actual answer text
            'option_a': question.option_a,
            'option_b': question.option_b,
            'option_c': question.option_c,
            'option_d': question.option_d
        })

    total_time = None
    if quiz_session.completed_at and quiz_session.started_at:
        total_time = quiz_session.completed_at - quiz_session.started_at

    return {
        'quiz_session_id': quiz_session.id,
        'category_id': quiz_session.category_id,
        'category_name': category.name if category else "Unknown",
        'difficulty_level': quiz_session.difficulty_level,
        'final_score': quiz_session.correct_answers,
        'total_questions': quiz_session.total_questions,
        'score_percentage': round((quiz_session.correct_answers / quiz_session.total_questions) * 100, 2),
        'xp_earned': quiz_session.xp_earned,
        'coins_earned': quiz_session.coins_earned,
        'total_time': str(total_time) if total_time else None,
        'total_time_seconds': quiz_session.total_time_seconds,
        'answers_breakdown': answers_breakdown,
        'performance_summary': {
            'accuracy': round((quiz_session.correct_answers / quiz_session.total_questions) * 100, 2),
            'average_time_per_question': round(quiz_session.total_time_seconds / quiz_session.total_questions, 2) if quiz_session.total_time_seconds else 0
        }
    }


@router.delete("/abandon/{quiz_session_id}")
def abandon_category_quiz(
    quiz_session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Abandon an active category quiz session"""

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

    return {"message": "Category quiz session abandoned successfully"}


@router.get("/active")
def get_active_category_quiz(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's current active category quiz session if any"""

    active_session = db.query(QuizSession).filter(
        QuizSession.user_id == current_user.id,
        QuizSession.is_active
    ).first()

    if not active_session:
        return {"message": "No active quiz session found", "active_session": None}

    # Get category information
    category = db.query(Category).filter(Category.id == active_session.category_id).first()

    return {
        "message": "Active category quiz session found",
        "active_session": {
            "quiz_session_id": active_session.id,
            "category_id": active_session.category_id,
            "category_name": category.name if category else "Unknown",
            "status": active_session.status.value,
            "questions_answered": active_session.questions_answered,
            "total_questions": active_session.total_questions,
            "current_score": active_session.correct_answers,
            "difficulty_level": active_session.difficulty_level
        }
    }


@router.get("/categories/{category_id}/stats")
def get_category_stats(category_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get user's performance statistics for a specific category"""

    # Validate category exists
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.is_active
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Get user's completed quizzes in this category
    completed_sessions = db.query(QuizSession).filter(
        QuizSession.user_id == current_user.id,
        QuizSession.category_id == category_id,
        QuizSession.status == SessionStatus.COMPLETED
    ).all()

    if not completed_sessions:
        return {
            "category_id": category_id,
            "category_name": category.name,
            "message": "No completed quizzes found for this category",
            "stats": None
        }

    # Calculate statistics
    total_quizzes = len(completed_sessions)
    total_questions = sum(session.total_questions for session in completed_sessions)
    total_correct = sum(session.correct_answers for session in completed_sessions)
    total_xp = sum(session.xp_earned for session in completed_sessions)
    total_coins = sum(session.coins_earned for session in completed_sessions)

    best_score = max(session.correct_answers / session.total_questions for session in completed_sessions) * 100
    average_score = (total_correct / total_questions) * 100 if total_questions > 0 else 0

    return {
        "category_id": category_id,
        "category_name": category.name,
        "stats": {
            "total_quizzes_completed": total_quizzes,
            "total_questions_answered": total_questions,
            "total_correct_answers": total_correct,
            "average_score_percentage": round(average_score, 2),
            "best_score_percentage": round(best_score, 2),
            "total_xp_earned": total_xp,
            "total_coins_earned": total_coins
        }
    }














































































