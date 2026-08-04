from models.transaction import Transaction
from models.user import User
from models.balance import Balance
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from models.enums import TransactionType

def get_all_transactions(session: Session) -> List[Transaction]:
    """
    Retrieve all transactions with their users.
    
    Args:
        session: Database session
    
    Returns:
        List[Transaction]: List of all transactions
    """
    try:
        statement = select(Transaction).options(
            selectinload(Transaction.user)
        )
        transactions = session.exec(statement).all()
        return transactions
    except Exception as e:
        raise

def get_transaction_by_id(transaction_id: int, session: Session) -> Optional[Transaction]:
    """
    Get transaction by ID.
    
    Args:
        transaction_id: Transaction ID to find
        session: Database session
    
    Returns:
        Optional[Transaction]: Found transaction or None
    """
    try:
        statement = select(Transaction).where(Transaction.id == transaction_id).options(
            selectinload(Transaction.user)
        )
        transaction = session.exec(statement).first()
        return transaction
    except Exception as e:
        raise

def get_transactions_by_user_id(user_id: int, session: Session) -> List[Transaction]:
    """
    Get all transactions for a specific user.
    
    Args:
        user_id: User ID to find transactions for
        session: Database session
    
    Returns:
        List[Transaction]: List of user's transactions
    """
    try:
        statement = select(Transaction).where(Transaction.user_id == user_id).options(
            selectinload(Transaction.user)
        )
        transactions = session.exec(statement).all()
        return transactions
    except Exception as e:
        raise

def get_transactions_by_status(status: str, session: Session) -> List[Transaction]:
    """
    Get transactions by status.
    
    Args:
        status: Transaction status (pending, approved, rejected)
        session: Database session
    
    Returns:
        List[Transaction]: List of transactions with given status
    """
    try:
        statement = select(Transaction).where(Transaction.status == status).options(
            selectinload(Transaction.user)
        )
        transactions = session.exec(statement).all()
        return transactions
    except Exception as e:
        raise

def get_pending_transactions(session: Session) -> List[Transaction]:
    """
    Get all pending transactions.
    
    Args:
        session: Database session
    
    Returns:
        List[Transaction]: List of pending transactions
    """
    try:
        statement = select(Transaction).where(Transaction.status == "pending").options(
            selectinload(Transaction.user)
        )
        transactions = session.exec(statement).all()
        return transactions
    except Exception as e:
        raise

def get_transactions_by_type(transaction_type: TransactionType, session: Session) -> List[Transaction]:
    """
    Get transactions by type.
    
    Args:
        transaction_type: Transaction type (DEPOSIT or WITHDRAW)
        session: Database session
    
    Returns:
        List[Transaction]: List of transactions with given type
    """
    try:
        statement = select(Transaction).where(Transaction.transaction_type == transaction_type).options(
            selectinload(Transaction.user)
        )
        transactions = session.exec(statement).all()
        return transactions
    except Exception as e:
        raise

def get_transactions_by_date_range(start_date: datetime, end_date: datetime, session: Session) -> List[Transaction]:
    """
    Get transactions within date range.
    
    Args:
        start_date: Start date
        end_date: End date
        session: Database session
    
    Returns:
        List[Transaction]: List of transactions in date range
    """
    try:
        statement = select(Transaction).where(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).options(
            selectinload(Transaction.user)
        )
        transactions = session.exec(statement).all()
        return transactions
    except Exception as e:
        raise

def create_transaction(transaction: Transaction, session: Session) -> Transaction:
    """
    Create new transaction.
    
    Args:
        transaction: Transaction to create
        session: Database session
    
    Returns:
        Transaction: Created transaction with ID
    """
    try:
        # Validate transaction
        transaction.validate()
        
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        
        return get_transaction_by_id(transaction.id, session)
    except Exception as e:
        session.rollback()
        raise

def approve_transaction(transaction_id: int, session: Session) -> Optional[Transaction]:
    """
    Approve a pending transaction.
    
    Args:
        transaction_id: Transaction ID to approve
        session: Database session
    
    Returns:
        Optional[Transaction]: Approved transaction or None
    
    Raises:
        ValueError: If transaction is not pending or not a deposit
    """
    try:
        transaction = get_transaction_by_id(transaction_id, session)
        if not transaction:
            return None
        
        # Check if transaction is pending
        if transaction.status != "pending":
            raise ValueError("Only pending transactions can be approved")
        
        # Check if transaction is deposit
        if transaction.transaction_type != TransactionType.DEPOSIT:
            raise ValueError("Only deposit transactions can be approved")
        
        # Approve transaction
        transaction.approve()
        
        # Update user's balance
        user = session.get(User, transaction.user_id)
        if user and user.balance:
            credits = Balance.rub_to_credits(float(transaction.amount))
            user.balance.deposit(credits)
            session.add(user.balance)
        
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        
        return get_transaction_by_id(transaction_id, session)
    except Exception as e:
        session.rollback()
        raise

def reject_transaction(transaction_id: int, session: Session) -> Optional[Transaction]:
    """
    Reject a pending transaction.
    
    Args:
        transaction_id: Transaction ID to reject
        session: Database session
    
    Returns:
        Optional[Transaction]: Rejected transaction or None
    
    Raises:
        ValueError: If transaction is not pending
    """
    try:
        transaction = get_transaction_by_id(transaction_id, session)
        if not transaction:
            return None
        
        # Check if transaction is pending
        if transaction.status != "pending":
            raise ValueError("Only pending transactions can be rejected")
        
        # Reject transaction
        transaction.reject()
        
        session.add(transaction)
        session.commit()
        session.refresh(transaction)
        
        return get_transaction_by_id(transaction_id, session)
    except Exception as e:
        session.rollback()
        raise

def delete_transaction(transaction_id: int, session: Session) -> bool:
    """
    Delete transaction by ID.
    
    Args:
        transaction_id: Transaction ID to delete
        session: Database session
    
    Returns:
        bool: True if deleted, False if not found
    """
    try:
        transaction = get_transaction_by_id(transaction_id, session)
        if transaction:
            session.delete(transaction)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        raise

def delete_transactions_by_user_id(user_id: int, session: Session) -> int:
    """
    Delete all transactions for a user.
    
    Args:
        user_id: User ID to delete transactions for
        session: Database session
    
    Returns:
        int: Number of deleted transactions
    """
    try:
        statement = select(Transaction).where(Transaction.user_id == user_id)
        transactions = session.exec(statement).all()
        count = len(transactions)
        
        for transaction in transactions:
            session.delete(transaction)
        
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        raise

def get_user_transaction_summary(user_id: int, session: Session) -> dict:
    """
    Get transaction summary for a user.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        dict: Summary with total deposits, withdrawals, and transaction count
    """
    try:
        transactions = get_transactions_by_user_id(user_id, session)
        
        total_deposits = sum(
            t.amount for t in transactions 
            if t.transaction_type == TransactionType.DEPOSIT and t.status == "approved"
        )
        total_withdrawals = sum(
            t.amount for t in transactions 
            if t.transaction_type == TransactionType.WITHDRAW and t.status == "approved"
        )
        
        return {
            "total_deposits": total_deposits,
            "total_withdrawals": total_withdrawals,
            "transaction_count": len(transactions),
            "pending_count": len([t for t in transactions if t.status == "pending"]),
            "approved_count": len([t for t in transactions if t.status == "approved"]),
            "rejected_count": len([t for t in transactions if t.status == "rejected"])
        }
    except Exception as e:
        raise

def search_transactions(search_term: str, session: Session) -> List[Transaction]:
    """
    Search transactions by description or user email.
    
    Args:
        search_term: Search term
        session: Database session
    
    Returns:
        List[Transaction]: List of matching transactions
    """
    try:
        statement = select(Transaction).where(
            (Transaction.description.contains(search_term)) |
            (Transaction.user.has(User.email.contains(search_term)))
        ).options(
            selectinload(Transaction.user)
        )
        transactions = session.exec(statement).all()
        return transactions
    except Exception as e:
        raise

def count_transactions(session: Session) -> int:
    """
    Count total number of transactions.
    
    Args:
        session: Database session
    
    Returns:
        int: Number of transactions
    """
    try:
        statement = select(Transaction)
        count = len(session.exec(statement).all())
        return count
    except Exception as e:
        raise

def count_transactions_by_status(status: str, session: Session) -> int:
    """
    Count transactions by status.
    
    Args:
        status: Transaction status
        session: Database session
    
    Returns:
        int: Number of transactions with given status
    """
    try:
        statement = select(Transaction).where(Transaction.status == status)
        count = len(session.exec(statement).all())
        return count
    except Exception as e:
        raise