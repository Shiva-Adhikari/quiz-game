# Standard library imports
import uuid
from datetime import datetime, timedelta, timezone

# Third-party imports
from sqlalchemy.orm import Session
from fastapi import (
    APIRouter, Depends, HTTPException, Response,
    # Request
)

# Local imports
from src.utils.db import get_db
# from src.utils import send_email
from src.utils.generate_otp import generate_otp
from src.utils.hash_password import hash_password, verify_password
from src.models.authentication import (
    User, EmailVerification,
    UserSession
)
from src.schemas.authentication import LoginResponse, UserResponse, UserRegister, UserLogin


router = APIRouter(prefix='/authentication', tags=['Authentication'])


@router.post('/register', response_model=UserResponse)
def register(user: UserRegister, db: Session = Depends(get_db)) -> UserResponse:
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

    ''' # block otp for sending in development
    # send email
    sent_email = send_email(user.email, otp)
    if not sent_email:
        raise HTTPException(status_code=404, detail='Invalid email')
    '''
    print(f'otp: {otp}')

    # hash password
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
def verify_email(email: str, otp: int, db: Session = Depends(get_db)) -> dict:
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
        raise HTTPException(status_code=400, detail='No verification record found')

    # check otp expired and not expires
    if email_verification_table.is_used:
        raise HTTPException(status_code=400, detail='Otp already used')

    if (email_verification_table.expires_at and datetime.now(
            timezone.utc) > email_verification_table.expires_at):
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
            email_verification_table.token = None
            db.commit()
            raise HTTPException(
                status_code=429,
                detail='Otp Expired, Please request a new otp')

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
        user_credentials: UserLogin,
        response: Response,
        db: Session = Depends(get_db)) -> LoginResponse:

    user_table = db.query(User).filter(
        User.username == user_credentials.username
    ).filter(User.is_verified).first()

    if not user_table:
        raise HTTPException(status_code=404, detail='User not found')

    verified_password = verify_password(
        user_credentials.password, user_table.password)

    if not verified_password:
        raise HTTPException(status_code=401, detail='Password not match')

    session_id = str(uuid.uuid4())
    new_session = UserSession(
        user_id=user_table.id,
        session_token=session_id,
        is_active=True,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )

    user_table.is_active = True
    db.add(new_session)
    db.commit()

    # response
    response.set_cookie(key='session_id', value=session_id, httponly=True)

    # Add password verification logic here
    return LoginResponse(
        message='Login Sucessful',
        user=UserResponse.from_orm(user_table)
    )


# @router.post('/logout')
# def logout(request: Request, db: Session = Depends(get_db)):
#     session_id = request.cookies.get('session_id')
#     if not session_id:
#         raise HTTPException(status_code=404, detail='Invalid session')

#     session = db.query(UserSession).filter(UserSession.session_token == session_id).first()
#     if session:
#         db.delete(session)
#         db.commit()

#     response = Response(status_code=200)
#     response.delete_cookie('session_id')
#     return response
