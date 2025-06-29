# Standard library imports
from datetime import datetime, timedelta, timezone

# Third-party imports
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

# Local imports
from src.utils.db import get_db
from src.utils.email_send import send_email
from src.utils.generate_otp import generate_otp
from src.models.user import User, EmailVerification
from src.utils.hash_password import hash_password, verify_password
from src.schemas.user import LoginResponse, UserResponse, UserCreate, UserLogin


router = APIRouter(prefix='/users', tags=['users'])


@router.post('/register', response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).filter(User.is_verified).first()

    if existing_user:
        if existing_user.email == user.email:
            raise HTTPException(status_code=409, detail='Email already exists')
        if existing_user.username == user.username:
            raise HTTPException(
                status_code=409, detail='Username already exists')

    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # send email
    sent_email = send_email(user.email, otp)
    if not sent_email:
        raise HTTPException(status_code=404, detail='Invalid email')

    # hash the password
    hashed_password = hash_password(user.password)

    try:
        # create new user
        user_table = User(
            email=user.email,
            username=user.username,
            password=hashed_password,
        )
        db.add(user_table)
        db.flush()  # Get the ID without committing

        email_verification_table = EmailVerification(
            user_id=user_table.id,
            token=otp,
            expires_at=expires_at,
        )
        db.add(email_verification_table)

        # commit both together
        db.commit()
        db.refresh(user_table)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f'Something went wrong {e}')

    return UserResponse.from_orm(user_table)


@router.post('/verify-email')
def verify_email(email: str, otp: int, db: Session = Depends(get_db)):
    user_table = db.query(User).filter(User.email == email).first()
    if not user_table:
        raise HTTPException(status_code=404, detail='User not found')

    if user_table.is_verified:
        return {'message': 'User already verified'}

    email_verification_table = db.query(EmailVerification).filter(
        EmailVerification.user_id == user_table.id
    ).first()

    # Check if verification record exists FIRST
    if not email_verification_table:
        raise HTTPException(
            status_code=400, detail='No verification record found')

    # check otp expired and not expires
    if email_verification_table.is_used:
        raise HTTPException(status_code=400, detail='Otp already used')

    if (email_verification_table.expires_at and
            datetime.now(timezone.utc) > email_verification_table.expires_at):
        # cleanup expired otp
        email_verification_table.token = None
        email_verification_table.expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail='Otp Expired')

    if email_verification_table.token != otp:
        email_verification_table.attempts += 1
        db.commit()

        remaining = 5 - email_verification_table.attempts
        if remaining > 0:
            raise HTTPException(
                status_code=400,
                detail=f'Invalid Otp, {remaining} attempts remaining')
        else:
            raise HTTPException(
                status_code=429,
                detail='Too many failed attempts. Please request a new otp')

    # Success - verify user and cleanup
    user_table.is_verified = True
    email_verification_table.token = None
    email_verification_table.expires_at = None
    email_verification_table.is_used = True
    email_verification_table.verified_at = datetime.now(timezone.utc)
    db.commit()

    return {'message': 'Email verified successfully'}


@router.post('/login', response_model=LoginResponse)
def login(
        user_credentials: UserLogin, db: Session = Depends(get_db)
        ) -> LoginResponse:
    user_table = db.query(User).filter(
        User.username == user_credentials.username
    ).filter(User.is_verified).first()

    if not user_table:
        raise HTTPException(status_code=404, detail='User not found')

    verified_password = verify_password(
        user_credentials.password, user_table.password)

    if not verified_password:
        raise HTTPException(status_code=404, detail='Password not match')

    user_table.is_active = True
    db.commit()

    # Add password verification logic here
    return LoginResponse(
        message='Login Sucessful',
        user=UserResponse.from_orm(user_table)
    )
