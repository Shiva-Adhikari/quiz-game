# === Standard library imports ===
import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone

# === Third-party imports ===
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from python_usernames import is_safe_username
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, HTTPException, Response, Request, Header, Cookie

# === Local imports ===
from src.utils.db import get_db
from src.utils.log import logger
# from src.utils.email_send import send_email
from src.utils.generate_otp import generate_otp
from src.utils.get_current_user import get_current_user
from src.core.reserved_usernames import RESERVED_USERNAMES
from src.utils.hash_password import hash_password, verify_password
from src.models.authentication import User, EmailVerification, UserSession
from src.schemas.authentication import LoginResponse, UserResponse, UserRegister, UserLogin


router = APIRouter(prefix='/authentication', tags=['Authentication'])
security = HTTPBearer(auto_error=False)


# Add this new endpoint BEFORE your /register endpoint
@router.get('/check-username/{username}')
async def check_username_availability(username: str, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Check if username is available and not blocked
    """
    username_lower = username.lower().strip()
    
    # Check minimum length
    if len(username_lower) < 4:
        return {
            "available": False,
            "message": "Username must be at least 4 characters"
        }
    
    # Check maximum length
    if len(username_lower) > 50:
        return {
            "available": False,
            "message": "Username must be less than 50 characters"
        }
    
    # Check using python-usernames library (checks for inappropriate words and URL-unsafe characters)
    if not is_safe_username(
        username_lower,
        blacklist=RESERVED_USERNAMES,
        max_length=50
    ):
        return {
            "available": False,
            "message": "This username is not allowed"
        }
    
    # Check if username exists in database
    query = select(User).where(User.username == username_lower)
    existing_user = await db.scalar(query)
    
    if existing_user:
        return {
            "available": False,
            "message": "Username already taken"
        }
    
    return {
        "available": True,
        "message": "Username is available"
    }


@router.post('/register', response_model=UserResponse)
async def register(user: UserRegister, db: Session = Depends(get_db)) -> UserResponse:

    # Add validation at the start
    from python_usernames import is_safe_username
    
    if not is_safe_username(
        user.username,
        blacklist=CUSTOM_BLOCKED_USERNAMES,
        max_length=50
    ):
        raise HTTPException(status_code=400, detail='Username is not allowed')

    query = select(User).where((User.email == user.email) | (User.username == user.username))
    existing_user = await db.scalar(query)

    if existing_user:
        if existing_user.is_verified:
            if existing_user.email == user.email:
                raise HTTPException(status_code=409, detail='Email already exists')
            if existing_user.username == user.username:
                raise HTTPException(status_code=409, detail='Username already exists')
        else:
            await db.delete(existing_user)
            await db.flush()

    otp = generate_otp()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    ''' # === block otp for sending in development ===
    # === send email ===
    from src.utils.email_send import send_email
    sent_email = send_email(user.email, otp)
    if not sent_email:
        raise HTTPException(status_code=404, detail='Invalid email')
    '''
    logger.debug(f'otp: {otp}')

    # hash password
    hashed_password = hash_password(user.password)

    try:
        #  create new user 
        user_table = User(
            email=user.email,
            username=user.username,
            password=hashed_password,
        )
        db.add(user_table)
        await db.flush()  # Get the ID without committing

        email_verification_table = EmailVerification(
            user_id=user_table.id,
            token=otp,
            expires_at=expires_at,
        )
        db.add(email_verification_table)

        #  Auto-create user profile 
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
        await db.commit()
        await db.refresh(user_table)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, detail=f'Something went wrong {e}')

    return UserResponse.from_orm(user_table)


@router.post('/verify-email')
async def verify_email(email: str, otp: int, db: Session = Depends(get_db)) -> dict:

    query = select(User).filter(User.email == email)
    user_table = await db.scalar(query)

    if not user_table:
        raise HTTPException(status_code=404, detail='User not found')

    if user_table.is_verified:
        return {'message': 'User already verified'}
    
    query = select(EmailVerification).where(EmailVerification.user_id == user_table.id)
    email_verification_table = await db.scalar(query)

    #  Check if verification record exists FIRST 
    if not email_verification_table:
        raise HTTPException(status_code=400, detail='No verification record found')

    #  check otp expired and not expires 
    if email_verification_table.is_used:
        raise HTTPException(status_code=400, detail='Otp already used')

    if (email_verification_table.expires_at and datetime.now(
            timezone.utc) > email_verification_table.expires_at):
        # cleanup expired otp
        email_verification_table.token = None
        email_verification_table.expires_at = None
        await db.commit()
        raise HTTPException(status_code=400, detail='Otp Expired')

    if int(email_verification_table.token) != int(otp):
        email_verification_table.attempts += 1
        await db.commit()

        remaining = 5 - email_verification_table.attempts
        if remaining > 0:
            raise HTTPException(
                status_code=400,
                detail=f'Invalid Otp, {remaining} attempts remaining')
        else:
            email_verification_table.token = None
            await db.commit()
            raise HTTPException(
                status_code=429,
                detail='Otp Expired, Please request a new otp')

    #  Success - verify user and cleanup 
    user_table.is_verified = True
    email_verification_table.token = None
    email_verification_table.expires_at = None
    email_verification_table.is_used = True
    email_verification_table.verified_at = datetime.now(timezone.utc)
    await db.commit()

    return {'message': 'Email verified successfully'}


@router.post('/login', response_model=LoginResponse)
async def login(
        user_credentials: UserLogin,
        response: Response,
        user_agent: Optional[str] = Header(None),
        db: Session = Depends(get_db)) -> LoginResponse:

    query = select(User).where(
        or_(
            User.username == user_credentials.username,
            User.email == user_credentials.username
        )
    ).where(User.is_verified)
    user_table = await db.scalar(query)

    if not user_table:
        raise HTTPException(status_code=404, detail='User not found')

    verified_password = verify_password(
        user_credentials.password, user_table.password)

    if not verified_password:
        raise HTTPException(status_code=400, detail='Password not match')

    session_id = str(uuid.uuid4())

    # Detect if mobile app (you can customize this detection)
    # is_mobile_app = user_agent and ('okhttp' in user_agent.lower() or 'android' in user_agent.lower() or 'ios' in user_agent.lower())
    is_mobile_app = user_agent and (
        'okhttp' in user_agent.lower() or 
        'android' in user_agent.lower() or 
        'ios' in user_agent.lower() or
        'dart' in user_agent.lower() or  # ADD THIS
        'flutter' in user_agent.lower() or  # ADD THIS
        'brainbattle' in user_agent.lower()  # Our custom user agent
    )

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
    await db.commit()

    # '''
    #  Set cookie for web browsers (not mobile apps) 
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
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_id: Optional[str] = Cookie(None, alias="session_id"),  # Use Cookie here
    db: Session = Depends(get_db)
):

    #  Get session token 
    session_token = None
    if credentials:
        session_token = credentials.credentials
    elif session_id:
        session_token = session_id

    if session_token:
        #  Deactivate session 
        query = select(UserSession).where(UserSession.session_token == session_token)
        session = await db.scalar(query)

        if session:
            session.is_active = False
            await db.commit()

    #  Clear cookie 
    response.delete_cookie(key='session_id')

    return {'message': 'Logout successful'}


@router.get('/session-status')
async def session_status(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    db: Session = Depends(get_db)
):
    session_token = None
    client_type = "web"

    #  Try to get token from Authorization header (mobile) 
    if credentials:
        session_token = credentials.credentials
        client_type = "mobile"

    #  If no token in header, try cookie (web) 
    elif session_id:
        session_token = session_id
        client_type = "web"

    #  No session found 
    if not session_token:
        return {
            "status": "no_session",
            "client_type": client_type
        }

    #  Find session in database 
    query = select(UserSession).where(UserSession.session_token == session_token)
    session = await db.scalar(query)

    if not session:
        return {
            "status": "invalid_session",
            "client_type": client_type
        }

    #  Check if session is expired 
    if session.expires_at < datetime.now(timezone.utc):
        # Mark session as inactive if expired
        session.is_active = False
        await db.commit()
        return {
            "status": "expired_session",
            "client_type": client_type
        }

    #  Check if session is active 
    if not session.is_active:
        return {
            "status": "inactive_session",
            "client_type": client_type
        }

    #  Get user information 
    query = select(User).where(User.id == session.user_id)
    user = await db.scalar(query)

    if not user:
        return {
            "status": "user_not_found",
            "client_type": client_type
        }

    #  Return valid session info 
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
