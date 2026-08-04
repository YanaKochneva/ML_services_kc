from models.balance import Balance
from models.user import User
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from decimal import Decimal

def get_balance_by_user_id(user_id: int, session: Session) -> Optional[Balance]:
    """
    Get balance by user ID.
    
    Args:
        user_id: User ID to find balance for
        session: Database session
    
    Returns:
        Optional[Balance]: Found balance or None
    """
    try:
        statement = select(Balance).where(Balance.user_id == user_id).options(
            selectinload(Balance.user)
        )
        balance = session.exec(statement).first()
        return balance
    except Exception as e:
        raise

def get_balance_by_id(balance_id: int, session: Session) -> Optional[Balance]:
    """
    Get balance by ID.
    
    Args:
        balance_id: Balance ID to find
        session: Database session
    
    Returns:
        Optional[Balance]: Found balance or None
    """
    try:
        statement = select(Balance).where(Balance.id == balance_id).options(
            selectinload(Balance.user)
        )
        balance = session.exec(statement).first()
        return balance
    except Exception as e:
        raise

def create_balance(user_id: int, session: Session) -> Balance:
    """
    Create new balance for user.
    
    Args:
        user_id: User ID to create balance for
        session: Database session
    
    Returns:
        Balance: Created balance
    
    Raises:
        ValueError: If user doesn't exist or balance already exists
    """
    try:
        # Check if user exists
        user = session.get(User, user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Check if balance already exists
        existing = get_balance_by_user_id(user_id, session)
        if existing:
            raise ValueError(f"Balance already exists for user {user_id}")
        
        # Create new balance
        balance = Balance(
            user_id=user_id,
            credits=Decimal('0')
        )
        
        # Validate balance
        balance.validate()
        
        session.add(balance)
        session.commit()
        session.refresh(balance)
        
        return get_balance_by_id(balance.id, session)
    except Exception as e:
        session.rollback()
        raise

def update_balance(balance_id: int, credits: Decimal, session: Session) -> Optional[Balance]:
    """
    Update balance credits.
    
    Args:
        balance_id: Balance ID to update
        credits: New credits amount
        session: Database session
    
    Returns:
        Optional[Balance]: Updated balance or None
    """
    try:
        balance = get_balance_by_id(balance_id, session)
        if not balance:
            return None
        
        balance.credits = credits
        
        # Validate updated balance
        balance.validate()
        
        session.add(balance)
        session.commit()
        session.refresh(balance)
        
        return get_balance_by_id(balance_id, session)
    except Exception as e:
        session.rollback()
        raise

def deposit_credits(user_id: int, amount: Decimal, session: Session) -> Optional[Balance]:
    """
    Deposit credits to user's balance.
    
    Args:
        user_id: User ID
        amount: Amount of credits to deposit
        session: Database session
    
    Returns:
        Optional[Balance]: Updated balance or None
    """
    try:
        balance = get_balance_by_user_id(user_id, session)
        if not balance:
            # Create balance if doesn't exist
            balance = create_balance(user_id, session)
        
        balance.deposit(amount)
        balance.validate()
        
        session.add(balance)
        session.commit()
        session.refresh(balance)
        
        return get_balance_by_user_id(user_id, session)
    except Exception as e:
        session.rollback()
        raise

def withdraw_credits(user_id: int, amount: Decimal, session: Session) -> Optional[Balance]:
    """
    Withdraw credits from user's balance.
    
    Args:
        user_id: User ID
        amount: Amount of credits to withdraw
        session: Database session
    
    Returns:
        Optional[Balance]: Updated balance or None
    
    Raises:
        ValueError: If insufficient balance
    """
    try:
        balance = get_balance_by_user_id(user_id, session)
        if not balance:
            raise ValueError(f"Balance not found for user {user_id}")
        
        balance.withdraw(amount)
        balance.validate()
        
        session.add(balance)
        session.commit()
        session.refresh(balance)
        
        return get_balance_by_user_id(user_id, session)
    except Exception as e:
        session.rollback()
        raise

def delete_balance(balance_id: int, session: Session) -> bool:
    """
    Delete balance by ID.
    
    Args:
        balance_id: Balance ID to delete
        session: Database session
    
    Returns:
        bool: True if deleted, False if not found
    """
    try:
        balance = get_balance_by_id(balance_id, session)
        if balance:
            session.delete(balance)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise

def delete_balance_by_user_id(user_id: int, session: Session) -> bool:
    """
    Delete balance by user ID.
    
    Args:
        user_id: User ID to delete balance for
        session: Database session
    
    Returns:
        bool: True if deleted, False if not found
    """
    try:
        balance = get_balance_by_user_id(user_id, session)
        if balance:
            session.delete(balance)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise

def get_all_balances(session: Session) -> List[Balance]:
    """
    Retrieve all balances with their users.
    
    Args:
        session: Database session
    
    Returns:
        List[Balance]: List of all balances
    """
    try:
        statement = select(Balance).options(
            selectinload(Balance.user)
        )
        balances = session.exec(statement).all()
        return balances
    except Exception as e:
        raise

def get_balances_with_min_credits(min_credits: Decimal, session: Session) -> List[Balance]:
    """
    Get all balances with credits >= min_credits.
    
    Args:
        min_credits: Minimum credits threshold
        session: Database session
    
    Returns:
        List[Balance]: List of balances meeting the criteria
    """
    try:
        statement = select(Balance).where(Balance.credits >= min_credits).options(
            selectinload(Balance.user)
        )
        balances = session.exec(statement).all()
        return balances
    except Exception as e:
        raise

def get_balances_with_zero_credits(session: Session) -> List[Balance]:
    """
    Get all balances with zero credits.
    
    Args:
        session: Database session
    
    Returns:
        List[Balance]: List of balances with zero credits
    """
    try:
        statement = select(Balance).where(Balance.credits == 0).options(
            selectinload(Balance.user)
        )
        balances = session.exec(statement).all()
        return balances
    except Exception as e:
        raise

def get_total_credits(session: Session) -> Decimal:
    """
    Get total credits across all users.
    
    Args:
        session: Database session
    
    Returns:
        Decimal: Total credits
    """
    try:
        statement = select(Balance)
        balances = session.exec(statement).all()
        total = sum(balance.credits for balance in balances)
        return total
    except Exception as e:
        raise

def get_average_credits(session: Session) -> Decimal:
    """
    Get average credits per user.
    
    Args:
        session: Database session
    
    Returns:
        Decimal: Average credits
    """
    try:
        statement = select(Balance)
        balances = session.exec(statement).all()
        if not balances:
            return Decimal('0')
        total = sum(balance.credits for balance in balances)
        return total / len(balances)
    except Exception as e:
        raise