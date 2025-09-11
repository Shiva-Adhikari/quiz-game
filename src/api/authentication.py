# === Standard library imports ===
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

# === Third-party imports ===
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import (
    APIRouter, Depends, HTTPException, Response,
    Request, Header, Cookie
)

# === Local imports===
from src.utils.db import get_db
from src.utils.email_send import send_email
from src.utils.generate_otp import generate_otp
from src.utils.hash_password import hash_password, verify_password
from src.models.authentication import (
    User, EmailVerification,
    UserSession
)
from src.schemas.authentication import LoginResponse, UserResponse, UserRegister, UserLogin
from src.utils.get_current_user import get_current_user


router = APIRouter(prefix='/authentication', tags=['Authentication'])
security = HTTPBearer(auto_error=False)


@router.post('/register', response_model=UserResponse)
def register(user: UserRegister, db: Session = Depends(get_db)) -> UserResponse:
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()

    if existing_user:
        if existing_user.is_verified:
            if existing_user.email == user.email:
                raise HTTPException(status_code=409, detail='Email already exists')
            if existing_user.username == user.username:
                raise HTTPException(status_code=409, detail='Username already exists')
        else:
            db.delete(existing_user)
            db.flush()

    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    ''' # === block otp for sending in development ===
    # === send email ===
    sent_email = send_email(user.email, otp)
    if not sent_email:
        raise HTTPException(status_code=404, detail='Invalid email')
    '''
    print(f'otp: {otp}')

    # hash password
    hashed_password = hash_password(user.password)

    try:
        # === create new user ===
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

        # === Auto-create user profile ===
        from src.models.user_profile import UserProfile  # Import your UserProfile model

        user_profile = UserProfile(
            user_id=user_table.id,
            display_name=user.username,  # Use their username as display_name
            total_xp=0,
            current_level=1,
            coins=0,
            total_games_played=0
        )
        db.add(user_profile)

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

    # === Check if verification record exists FIRST ===
    if not email_verification_table:
        raise HTTPException(status_code=400, detail='No verification record found')

    # === check otp expired and not expires ===
    if email_verification_table.is_used:
        raise HTTPException(status_code=400, detail='Otp already used')

    if (email_verification_table.expires_at and datetime.now(
            timezone.utc) > email_verification_table.expires_at):
        # cleanup expired otp
        email_verification_table.token = None
        email_verification_table.expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail='Otp Expired')

    if int(email_verification_table.token) != int(otp):
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

    # === Success - verify user and cleanup ===
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
        user_agent: Optional[str] = Header(None),
        db: Session = Depends(get_db)) -> LoginResponse:

    user_table = db.query(User).filter(
        or_(
            User.username == user_credentials.username,
            User.email == user_credentials.username
        )
    ).filter(User.is_verified).first()

    if not user_table:
        raise HTTPException(status_code=404, detail='User not found')

    verified_password = verify_password(
        user_credentials.password, user_table.password)

    if not verified_password:
        raise HTTPException(status_code=401, detail='Password not match')

    session_id = str(uuid.uuid4())

    # Detect if mobile app (you can customize this detection)
    is_mobile_app = user_agent and ('okhttp' in user_agent.lower() or 'android' in user_agent.lower() or 'ios' in user_agent.lower())
    print(f'\n\n\ntype of is_mobile: {type(is_mobile_app)} and value: {is_mobile_app}\n\n')

    new_session = UserSession(
        user_id=user_table.id,
        session_token=session_id,
        is_active=True,
        is_mobile=is_mobile_app,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)   # longer session for 7 days
    )

    user_table.is_active = True
    db.add(new_session)
    db.commit()

    # '''
    # === Set cookie for web browsers (not mobile apps) ===
    if not is_mobile_app:
        response.set_cookie(
            key='session_id',
            value=session_id,
            httponly=True,
            secure=True,  # HTTPS only
            samesite='lax',
            max_age=7 * 24 * 60 * 60  # 7 days
        )
    # '''

    # response
    # response.set_cookie(key='session_id', value=session_id, httponly=True)

    # Response
    login_response = LoginResponse(
        message='Login Successful',
        user=UserResponse.from_orm(user_table)
    )

    # Mobile apps lai token return garcha
    if is_mobile_app:
        login_response.token = session_id  # Add token field to LoginResponse schema

    return login_response


@router.post('/logout')
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_id: Optional[str] = Cookie(None, alias="session_id"),  # Use Cookie here
    db: Session = Depends(get_db)
):

    # === Get session token ===
    session_token = None
    if credentials:
        session_token = credentials.credentials
    elif session_id:
        session_token = session_id

    if session_token:
        # === Deactivate session ===
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()
        if session:
            session.is_active = False
            db.commit()

    # === Clear cookie ===
    response.delete_cookie(key='session_id')

    return {'message': 'Logout successful'}


@router.get('/session-status')
def session_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    db: Session = Depends(get_db)
):
    session_token = None
    client_type = "web"

    # === Try to get token from Authorization header (mobile) ===
    if credentials:
        session_token = credentials.credentials
        client_type = "mobile"

    # === If no token in header, try cookie (web) ===
    elif session_id:
        session_token = session_id
        client_type = "web"

    # === No session found ===
    if not session_token:
        return {
            "status": "no_session",
            "client_type": client_type
        }

    # === Find session in database ===
    session = db.query(UserSession).filter(
        UserSession.session_token == session_token
    ).first()

    if not session:
        return {
            "status": "invalid_session",
            "client_type": client_type
        }

    # === Check if session is expired ===
    if session.expires_at < datetime.now(timezone.utc):
        # Mark session as inactive if expired
        session.is_active = False
        db.commit()
        return {
            "status": "expired_session",
            "client_type": client_type
        }

    # === Check if session is active ===
    if not session.is_active:
        return {
            "status": "inactive_session",
            "client_type": client_type
        }

    # === Get user information ===
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        return {
            "status": "user_not_found",
            "client_type": client_type
        }

    # === Return valid session info ===
    return {
        "status": "valid_session",
        "client_type": client_type,
        "is_mobile": session.is_mobile,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_verified": user.is_verified
        },
        "session": {
            "created_at": session.created_at,
            "expires_at": session.expires_at,
            "last_activity": session.last_activity_at if hasattr(session, 'last_activity_at') else None
        }
    }
