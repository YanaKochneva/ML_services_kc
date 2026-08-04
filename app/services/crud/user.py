from models.user import User
from models.transaction import Transaction
from models.ml_task import MLTask
from models.balance import Balance
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from decimal import Decimal

def get_all_users(session: Session) -> List[User]:
    """
    Retrieve all users with their relationships.
    
    Args:
        session: Database session
    
    Returns:
        List[User]: List of all users
    """
    try:
        statement = select(User).options(
            selectinload(User.balance),
            selectinload(User.transactions),
            selectinload(User.ml_tasks)
        )
        users = session.exec(statement).all()
        return users
    except Exception as e:
        raise

def get_user_by_id(user_id: int, session: Session) -> Optional[User]:
    """
    Get user by ID with all relationships.
    
    Args:
        user_id: User ID to find
        session: Database session
    
    Returns:
        Optional[User]: Found user or None
    """
    try:
        statement = select(User).where(User.id == user_id).options(
            selectinload(User.balance),
            selectinload(User.transactions),
            selectinload(User.ml_tasks)
        )
        user = session.exec(statement).first()
        return user
    except Exception as e:
        raise

def get_user_by_email(email: str, session: Session) -> Optional[User]:
    """
    Get user by email.
    
    Args:
        email: Email to search for
        session: Database session
    
    Returns:
        Optional[User]: Found user or None
    """
    try:
        statement = select(User).where(User.email == email).options(
            selectinload(User.balance),
            selectinload(User.transactions),
            selectinload(User.ml_tasks)
        )
        user = session.exec(statement).first()
        return user
    except Exception as e:
        raise

def get_user_by_username(username: str, session: Session) -> Optional[User]:
    """
    Get user by username.
    
    Args:
        username: Username to search for
        session: Database session
    
    Returns:
        Optional[User]: Found user or None
    """
    try:
        statement = select(User).where(User.username == username).options(
            selectinload(User.balance),
            selectinload(User.transactions),
            selectinload(User.ml_tasks)
        )
        user = session.exec(statement).first()
        return user
    except Exception as e:
        raise

def get_active_users(session: Session) -> List[User]:
    """
    Get all active users.
    
    Args:
        session: Database session
    
    Returns:
        List[User]: List of active users
    """
    try:
        statement = select(User).where(User.is_active == True).options(
            selectinload(User.balance),
            selectinload(User.transactions),
            selectinload(User.ml_tasks)
        )
        users = session.exec(statement).all()
        return users
    except Exception as e:
        raise

def create_user(user: User, session: Session) -> User:
    """
    Create new user with balance.
    
    Args:
        user: User to create
        session: Database session
    
    Returns:
        User: Created user with ID and relationships
    """
    try:
        # Validate user data
        user.validate()
        
        # Create balance for user
        balance = Balance(
            user_id=user.id,
            credits=Decimal('0')
        )
        user.balance = balance
        
        session.add(user)
        session.add(balance)
        session.commit()
        session.refresh(user)
        
        # Load relationships
        return get_user_by_id(user.id, session)
    except Exception as e:
        session.rollback()
        raise

def update_user(user_id: int, user_data: dict, session: Session) -> Optional[User]:
    """
    Update user information.
    
    Args:
        user_id: User ID to update
        user_data: Dictionary with updated fields
        session: Database session
    
    Returns:
        Optional[User]: Updated user or None
    """
    try:
        user = get_user_by_id(user_id, session)
        if not user:
            return None
        
        # Update fields
        for key, value in user_data.items():
            if hasattr(user, key) and key not in ['id', 'created_at']:
                setattr(user, key, value)
        
        # Validate updated user
        user.validate()
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return get_user_by_id(user_id, session)
    except Exception as e:
        session.rollback()
        raise

def delete_user(user_id: int, session: Session) -> bool:
    """
    Delete user by ID.
    
    Args:
        user_id: User ID to delete
        session: Database session
    
    Returns:
        bool: True if deleted, False if not found
    """
    try:
        user = get_user_by_id(user_id, session)
        if user:
            # Cascade will handle balance, transactions, and ml_tasks deletion
            session.delete(user)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise

def get_user_balance(user_id: int, session: Session) -> Optional[Decimal]:
    """
    Get user's current balance.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        Optional[Decimal]: User's balance or None
    """
    try:
        user = get_user_by_id(user_id, session)
        if user and user.balance:
            return user.balance.credits
        return None
    except Exception as e:
        raise

def get_user_transactions(user_id: int, session: Session) -> List[Transaction]:
    """
    Get all transactions for a user.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        List[Transaction]: List of user's transactions
    """
    try:
        user = get_user_by_id(user_id, session)
        if user:
            return user.transactions
        return []
    except Exception as e:
        raise

def get_user_ml_tasks(user_id: int, session: Session) -> List[MLTask]:
    """
    Get all ML tasks for a user.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        List[MLTask]: List of user's ML tasks
    """
    try:
        user = get_user_by_id(user_id, session)
        if user:
            return user.ml_tasks
        return []
    except Exception as e:
        raise

def search_users(search_term: str, session: Session) -> List[User]:
    """
    Search users by username or email.
    
    Args:
        search_term: Search term
        session: Database session
    
    Returns:
        List[User]: List of matching users
    """
    try:
        statement = select(User).where(
            (User.username.contains(search_term)) | 
            (User.email.contains(search_term))
        ).options(
            selectinload(User.balance),
            selectinload(User.transactions),
            selectinload(User.ml_tasks)
        )
        users = session.exec(statement).all()
        return users
    except Exception as e:
        raise

def count_users(session: Session) -> int:
    """
    Count total number of users.
    
    Args:
        session: Database session
    
    Returns:
        int: Number of users
    """
    try:
        statement = select(User)
        count = len(session.exec(statement).all())
        return count
    except Exception as e:
        raise

def count_active_users(session: Session) -> int:
    """
    Count active users.
    
    Args:
        session: Database session
    
    Returns:
        int: Number of active users
    """
    try:
        statement = select(User).where(User.is_active == True)
        count = len(session.exec(statement).all())
        return count
    except Exception as e:
        raise