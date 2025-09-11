# Standard library imports
from typing import List, Optional

# Third-party imports
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query

# Local imports
from src.utils.db import get_db
from src.models.questions import Category, Question
from src.schemas.questions import CategoryCreate, QuestionCreate


router = APIRouter(prefix='/question', tags=['Question'])


# ============================
# CREATE CATEGORIES
# ============================

@router.post('/category/insert')
def category_create(category_data: CategoryCreate, db: Session = Depends(get_db)) -> dict:
    """ insert category in database, one by one
    """

    category = db.query(Category).filter(Category.name == category_data.name).first()
    if category:
        raise HTTPException(status_code=401, detail='Category already present')

    new_category = Category(
        name=category_data.name.lower(),
        description=category_data.description.lower(),
        difficulty_multiplier=category_data.difficulty_multiplier,
        is_active=category_data.is_active
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    # Response formation
    return {
        "message": "Category created successfully",
        "category": {
            "id": new_category.id,
            "name": new_category.name,
            "description": new_category.description,
            "difficulty_multiplier": new_category.difficulty_multiplier,
            "is_active": new_category.is_active,
            "created_at": new_category.created_at
        }
    }


@router.post('/categories/insert/bulk')
def category_create_bulk(categories_data: List[CategoryCreate], db: Session = Depends(get_db)):
    """ insert bulk categories
    """

    if not categories_data:
        raise HTTPException(status_code=400, detail='At least one category is required')

    category_names = [cat.name for cat in categories_data]
    if len(categories_data) != len(set(category_names)):
        raise HTTPException(status_code=400, detail='Duplicate category name is present in request')

    existing_categories = db.query(Category).filter(Category.name.in_(category_names)).all()
    if existing_categories:
        existing_names = [cat.name for cat in existing_categories]
        raise HTTPException(status_code=409, detail=f'Categories already exists: {', '.join(existing_names)}')

    for category_data in categories_data:
        category = db.query(Category).filter(Category.name == category_data.name).first()
        if category:
            raise HTTPException(status_code=401, detail='Category already present')

    new_category = [
        Category(
            name=category_data.name.lower(),
            description=category_data.description.lower(),
            difficulty_multiplier=category_data.difficulty_multiplier,
            is_active=category_data.is_active
        ) for category_data in categories_data
    ]

    db.add_all(new_category)
    db.commit()

    for category in new_category:
        db.refresh(category)

    return {
        'message': f'Successfully created {len(new_category)} category',
        'categories_created': len(new_category),
        'questions': [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'difficulty_multiplier': c.difficulty_multiplier,
                'is_active': c.is_active,
                'created_at': c.created_at
            } for c in new_category
        ]
    }


# ============================
# READ CATEGORIES
# ============================

@router.get('/categories/read')
def get_categories(
    search: Optional[str] = Query(None, description="Search in category name or description"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get categories with search and pagination"""

    # Build query
    query = db.query(Category)

    # Apply search filter
    if search:
        search_filter = f"%{search.lower()}%"
        query = query.filter(
            or_(
                func.lower(Category.name).like(search_filter),
                func.lower(Category.description).like(search_filter)
            )
        )

    # Apply active status filter
    if is_active is not None:
        query = query.filter(Category.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    categories = query.offset(offset).limit(per_page).all()

    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1

    return {
        "message": "Categories retrieved successfully",
        "data": {
            "categories": [
                {
                    "id": cat.id,
                    "name": cat.name.capitalize(),
                    "description": cat.description.capitalize(),
                    "difficulty_multiplier": cat.difficulty_multiplier,
                    "is_active": cat.is_active,
                    "created_at": cat.created_at,
                    "questions_count": len(cat.questions)
                } for cat in categories
            ],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
    }


@router.get('/category/read/{category_id}')
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get single category by ID"""

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    return {
        "message": "Category retrieved successfully",
        "category": {
            "id": category.id,
            "name": category.name.capitalize(),
            "description": category.description.capitalize(),
            "difficulty_multiplier": category.difficulty_multiplier,
            "is_active": category.is_active,
            "created_at": category.created_at,
            "updated_at": category.updated_at,
            "questions_count": len(category.questions)
        }
    }


# ============================
# UPDATE CATEGORIES
# ============================

@router.put('/category/update/{category_id}')
def update_category(category_id: int, category_data: CategoryCreate, db: Session = Depends(get_db)):
    """Update single category"""

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    # Check if name already exists (excluding current category)
    existing_category = db.query(Category).filter(
        Category.name == category_data.name,
        Category.id != category_id
    ).first()
    if existing_category:
        raise HTTPException(status_code=409, detail='Category name already exists')

    # Update fields
    category.name = category_data.name
    category.description = category_data.description
    category.difficulty_multiplier = category_data.difficulty_multiplier
    category.is_active = category_data.is_active

    db.commit()
    db.refresh(category)

    return {
        "message": "Category updated successfully",
        "category": {
            "id": category.id,
            "name": category.name.lower(),
            "description": category.description.lower(),
            "difficulty_multiplier": category.difficulty_multiplier,
            "is_active": category.is_active,
            "updated_at": category.updated_at
        }
    }


# ============================
# DELETE CATEGORIES
# ============================

@router.delete('/category/delete/{category_id}')
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete single category (and all its questions due to CASCADE)"""

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    questions_count = len(category.questions)
    category_name = category.name

    db.delete(category)
    db.commit()

    return {
        "message": f"Category '{category_name}' and {questions_count} associated questions deleted successfully",
        "deleted_category_id": category_id,
        "deleted_questions_count": questions_count
    }


@router.delete('/categories/delete/bulk')
def delete_categories_bulk(category_ids: List[int], db: Session = Depends(get_db)):
    """Delete multiple categories"""

    if not category_ids:
        raise HTTPException(status_code=400, detail='At least one category ID is required')

    categories = db.query(Category).filter(Category.id.in_(category_ids)).all()
    if len(categories) != len(category_ids):
        found_ids = [cat.id for cat in categories]
        missing_ids = [cat_id for cat_id in category_ids if cat_id not in found_ids]
        raise HTTPException(status_code=404, detail=f'Categories not found: {missing_ids}')

    # Calculate questions count
    total_questions = sum(len(cat.questions) for cat in categories)
    category_names = [cat.name for cat in categories]

    # Delete categories (questions will be deleted due to CASCADE)
    db.query(Category).filter(Category.id.in_(category_ids)).delete(synchronize_session=False)
    db.commit()

    return {
        "message": f"Successfully deleted {len(categories)} categories and {total_questions} associated questions",
        "deleted_categories": category_names,
        "deleted_categories_count": len(categories),
        "deleted_questions_count": total_questions
    }


# ============================
# CREATE QUESTIONS
# ============================

@router.post('/question/insert/{category_id}')
def question_create(category_id: int, question_data: QuestionCreate, db: Session = Depends(get_db)) -> dict:
    """ insert question based on category id, one by one
    """

    category = db.query(Category).filter(Category.id == category_id, Category.is_active).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    new_question = Question(
        category_id=category_id,
        question_text=question_data.question_text.lower(),
        difficulty_level=question_data.difficulty_level,
        correct_answer=question_data.correct_answer.lower(),
        option_a=question_data.option_a.lower(),
        option_b=question_data.option_b.lower(),
        option_c=question_data.option_c.lower(),
        option_d=question_data.option_d.lower(),
        is_active=question_data.is_active
    )

    db.add(new_question)
    db.commit()
    db.refresh(new_question)

    return {
        'message': 'Question Added to category',
        'question': {
            'id': new_question.id,
            'category_id': new_question.category_id,
            'question_text': new_question.question_text,
            'difficulty_level': new_question.difficulty_level,
            'correct_answer': new_question.correct_answer,
            'is_active': new_question.is_active,
            'created_at': new_question.created_at
        }
    }


@router.post('/questions/insert/bulk/{category_id}')
def question_create_bulk(category_id: int, questions_data: List[QuestionCreate], db: Session = Depends(get_db)):
    """ insert bulk questions
    """

    category = db.query(Category).filter(Category.id == category_id, Category.is_active).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    new_questions = [
        Question(
            category_id=category_id,
            question_text=question_data.question_text.lower(),
            difficulty_level=question_data.difficulty_level,
            correct_answer=question_data.correct_answer.lower(),
            option_a=question_data.option_a.lower(),
            option_b=question_data.option_b.lower(),
            option_c=question_data.option_c.lower(),
            option_d=question_data.option_d.lower(),
            is_active=question_data.is_active
        ) for question_data in questions_data
    ]

    db.add_all(new_questions)
    db.commit()

    # Refresh to get id and timestamps
    for question in new_questions:
        db.refresh(question)

    return {
        'message': f'Successfully created {len(new_questions)} questions for category',
        'category_id': category_id,
        'category_name': category.name,
        'questions_created': len(new_questions),
        'questions': [
            {
                'id': q.id,
                'question_text': q.question_text,
                'difficulty_level': q.difficulty_level.value,
                'correct_answer': q.correct_answer,
                'is_active': q.is_active,
                'created_at': q.created_at
            } for q in new_questions
        ]
    }


# ============================
# READ QUESTIONS
# ============================

@router.get('/questions/read/bulk/{category_id}')
def get_category_questions(
    category_id: int,
    search: Optional[str] = Query(None, description="Search in question text"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    difficulty_level: Optional[str] = Query(None, description="Filter by difficulty level"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get questions for a category with search and pagination"""

    # Check if category exists
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    # Build query
    query = db.query(Question).filter(Question.category_id == category_id)

    # Apply search filter
    if search:
        search_filter = f"%{search.lower()}%"
        query = query.filter(func.lower(Question.question_text).like(search_filter))

    # Apply difficulty level filter
    if difficulty_level:
        try:
            from src.utils.enums import DifficultyLevel
            difficulty_enum = DifficultyLevel(difficulty_level.upper())
            query = query.filter(Question.difficulty_level == difficulty_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f'Invalid difficulty level: {difficulty_level}')

    # Apply active status filter
    if is_active is not None:
        query = query.filter(Question.is_active == is_active)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * per_page
    questions = query.offset(offset).limit(per_page).all()

    # Calculate pagination metadata
    total_pages = (total + per_page - 1) // per_page
    has_next = page < total_pages
    has_prev = page > 1

    return {
        "message": "Questions retrieved successfully",
        "data": {
            "category": {
                "id": category.id,
                "name": category.name
            },
            "questions": [
                {
                    "id": q.id,
                    "question_text": q.question_text.capitalize(),
                    "difficulty_level": q.difficulty_level.value,
                    "correct_answer": q.correct_answer.capitalize(),
                    "option_a": q.option_a.capitalize(),
                    "option_b": q.option_b.capitalize(),
                    "option_c": q.option_c.capitalize(),
                    "option_d": q.option_d.capitalize(),
                    "is_active": q.is_active,
                    "created_at": q.created_at
                } for q in questions
            ],
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total_items": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            }
        }
    }


@router.get('/questions/read/{question_id}')
def get_question(question_id: int, db: Session = Depends(get_db)):
    """Get single question by ID"""

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail='Question not found')

    return {
        "message": "Question retrieved successfully",
        "question": {
            "id": question.id,
            "category_id": question.category_id,
            "category_name": question.category.name.capitalize(),
            "question_text": question.question_text.capitalize(),
            "difficulty_level": question.difficulty_level.value,
            "correct_answer": question.correct_answer.capitalize(),
            "option_a": question.option_a.capitalize(),
            "option_b": question.option_b.capitalize(),
            "option_c": question.option_c.capitalize(),
            "option_d": question.option_d.capitalize(),
            "is_active": question.is_active,
            "created_at": question.created_at,
            "updated_at": question.updated_at
        }
    }


# ============================
# UPDATE QUESTIONS
# ============================

@router.put('/question/update/{question_id}')
def update_question(question_id: int, question_data: QuestionCreate, db: Session = Depends(get_db)):
    """Update single question"""

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail='Question not found')

    # Update fields
    question.question_text = question_data.question_text.lower()
    question.difficulty_level = question_data.difficulty_level
    question.correct_answer = question_data.correct_answer.lower()
    question.option_a = question_data.option_a.lower()
    question.option_b = question_data.option_b.lower()
    question.option_c = question_data.option_c.lower()
    question.option_d = question_data.option_d.lower()
    question.is_active = question_data.is_active

    db.commit()
    db.refresh(question)

    return {
        "message": "Question updated successfully",
        "question": {
            "id": question.id,
            "category_id": question.category_id,
            "question_text": question.question_text,
            "difficulty_level": question.difficulty_level.value,
            "correct_answer": question.correct_answer,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "is_active": question.is_active,
            "updated_at": question.updated_at
        }
    }


# ============================
# DELETE QUESTIONS
# ============================

@router.delete('/question/delete/{question_id}')
def delete_question(question_id: int, db: Session = Depends(get_db)):
    """Delete single question"""

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail='Question not found')

    question_text = question.question_text[:50] + "..." if len(question.question_text) > 50 else question.question_text

    db.delete(question)
    db.commit()

    return {
        "message": "Question deleted successfully",
        "deleted_question_id": question_id,
        "deleted_question_text": question_text
    }


@router.delete('/questions/delete/bulk')
def delete_questions_bulk(question_ids: List[int], db: Session = Depends(get_db)):
    """Delete multiple questions"""

    if not question_ids:
        raise HTTPException(status_code=400, detail='At least one question ID is required')

    questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
    if len(questions) != len(question_ids):
        found_ids = [q.id for q in questions]
        missing_ids = [q_id for q_id in question_ids if q_id not in found_ids]
        raise HTTPException(status_code=404, detail=f'Questions not found: {missing_ids}')

    # Delete questions
    db.query(Question).filter(Question.id.in_(question_ids)).delete(synchronize_session=False)
    db.commit()

    return {
        "message": f"Successfully deleted {len(questions)} questions",
        "deleted_questions_count": len(questions),
        "deleted_question_ids": question_ids
    }
