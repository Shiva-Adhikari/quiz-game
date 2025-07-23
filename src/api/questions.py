# Standard library imports
from typing import List
# from datetime import datetime, timedelta, timezone

# Third-party imports
# from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

# Local imports
from src.utils.db import get_db
from src.models.questions import Category, Question
from src.schemas.questions import CategoryCreate, QuestionCreate


router = APIRouter(prefix='/question', tags=['Question'])


@router.post('/categories')
def category_create(category_data: CategoryCreate, db: Session = Depends(get_db)) -> dict:
    """ insert category in database, one by one
    """

    category = db.query(Category).filter(Category.name == category_data.name).first()
    if category:
        raise HTTPException(status_code=401, detail='Category already present')

    new_category = Category(
        name=category_data.name,
        description=category_data.description,
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


@router.post('/categories/bulk')
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
            name=category_data.name,
            description=category_data.description,
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
                'name': c.name,
                'description': c.description,
                'difficulty_multiplier': c.difficulty_multiplier,
                'is_active': c.is_active,
                'created_at': c.created_at
            } for c in new_category
        ]
    }


@router.post('/categories/{category_id}/questions')
def question_create(category_id: int, question_data: QuestionCreate, db: Session = Depends(get_db)) -> dict:
    """ insert question based on category id, one by one
    """

    category = db.query(Category).filter(Category.id == category_id, Category.is_active).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    new_question = Question(
        category_id=category_id,
        question_text=question_data.question_text,
        correct_answer=question_data.correct_answer,
        option_a=question_data.option_a,
        option_b=question_data.option_b,
        option_c=question_data.option_c,
        option_d=question_data.option_d,
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
            'correct_answer': new_question.correct_answer,
            'is_active': new_question.is_active,
            'created_at': new_question.created_at
        }
    }


@router.post('/categories/{category_id}/questions/bulk')
def question_create_bulk(category_id: int, questions_data: List[QuestionCreate], db: Session = Depends(get_db)):
    """ insert bulk questions
    """

    category = db.query(Category).filter(Category.id == category_id, Category.is_active).first()
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')

    new_questions = [
        Question(
            category_id=category_id,
            question_text=question_data.question_text,
            correct_answer=question_data.correct_answer,
            option_a=question_data.option_a,
            option_b=question_data.option_b,
            option_c=question_data.option_c,
            option_d=question_data.option_d,
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
