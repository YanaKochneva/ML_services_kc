# routes/user_route.py
from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.user import User
from services.crud import user as UserService
from typing import List, Dict
import logging
from services.auth.auth import get_current_user, get_current_active_admin

# Configure logging
logger = logging.getLogger(__name__)

user_route = APIRouter()

@user_route.post(
    '/signup',
    response_model=Dict[str, str],
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with username, email and password"
)
async def signup(data: User, session=Depends(get_session)) -> Dict[str, str]:
    """
    Create new user account.

    Args:
        data: User registration data (username, email, password_hash)
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If user already exists
    """
    try:
        existing_user = UserService.get_user_by_email(data.email, session)
        if existing_user:
            logger.warning(f"Signup attempt with existing email: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        existing_username = UserService.get_user_by_username(data.username, session)
        if existing_username:
            logger.warning(f"Signup attempt with existing username: {data.username}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username already exists"
            )

        user = User(
            username=data.username,
            email=data.email,
            password_hash=data.password_hash,
            role=data.role if hasattr(data, 'role') else "USER"
        )
        UserService.create_user(user, session)
        logger.info(f"New user registered: {data.username} ({data.email})")
        return {"message": "User successfully registered"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )

@user_route.post(
    '/signin',
    response_model=Dict[str, str],
    summary="User Sign In",
    description="Authenticate existing user with email and password"
)
async def signin(data: User, session=Depends(get_session)) -> Dict[str, str]:
    """
    Authenticate existing user.

    Args:
        data: User credentials (email, password_hash)
        session: Database session

    Returns:
        dict: Success message with user info

    Raises:
        HTTPException: If authentication fails
    """
    # Ищем пользователя по email
    user = UserService.get_user_by_email(data.email, session)
    if user is None:
        logger.warning(f"Login attempt with non-existent email: {data.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )
    
    if user.password_hash != data.password_hash:
        logger.warning(f"Failed login attempt for user: {data.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Wrong credentials passed"
        )
    
    logger.info(f"User signed in: {user.username} ({user.email})")
    return {
        "message": "User signed in successfully",
        "user_id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role
    }

@user_route.get(
    "/me",
    response_model=User,
    summary="Get user profile"
)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
) -> User:
    return current_user

@user_route.get(
    "/get_all_users",
    response_model=List[User],
    summary="Get all users (admin only)"
)
async def get_all_users(
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> List[User]:
    return UserService.get_all_users(session)

@user_route.get(
    "/{user_id}",
    response_model=User,
    summary="Get user by ID"
)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> User:
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(403, "Not allowed")
    user = UserService.get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(404, "User not found")
    return user
