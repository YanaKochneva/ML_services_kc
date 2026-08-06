# routes/transaction_route.py
from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.transaction import Transaction
from models.user import User
from services.crud import transaction as TransactionService
from services.crud import user as UserService
from typing import List, Dict
import logging

# Configure logging
logger = logging.getLogger(__name__)

transaction_route = APIRouter()

@transaction_route.post(
    '/create',
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    summary="Create Transaction",
    description="Create a new transaction (deposit or withdrawal)"
)
async def create_transaction(
    data: Transaction,
    session=Depends(get_session)
) -> Transaction:
    """
    Create new transaction.

    Args:
        data: Transaction data (user_id, amount, transaction_type, description)
        session: Database session

    Returns:
        Transaction: Created transaction

    Raises:
        HTTPException: If user not found or validation fails
    """
    try:
        # Проверяем, существует ли пользователь
        user = UserService.get_user_by_id(data.user_id, session)
        if user is None:
            logger.warning(f"Transaction creation attempt for non-existent user: ID {data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        transaction = Transaction(
            user_id=data.user_id,
            amount=data.amount,
            transaction_type=data.transaction_type,
            description=data.description or "",
            status="pending"
        )
        
        created_transaction = TransactionService.create_transaction(transaction, session)
        logger.info(f"Transaction created: ID {created_transaction.id}, User ID: {data.user_id}, Amount: {data.amount}")
        return created_transaction

    except ValueError as e:
        logger.warning(f"Transaction validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating transaction"
        )

@transaction_route.get(
    '/user/{user_id}',
    response_model=List[Transaction],
    summary="Get Transactions by User",
    description="Get all transactions for a specific user"
)
async def get_user_transactions(
    user_id: int,
    session=Depends(get_session)
) -> List[Transaction]:
    """
    Get all transactions for a user.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        List[Transaction]: List of user transactions

    Raises:
        HTTPException: If user not found
    """
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        logger.warning(f"Get transactions attempt for non-existent user: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    transactions = TransactionService.get_transactions_by_user(user_id, session)
    logger.info(f"Retrieved {len(transactions)} transactions for user ID {user_id}")
    return transactions

@transaction_route.get(
    '/{transaction_id}',
    response_model=Transaction,
    summary="Get Transaction by ID",
    description="Get a specific transaction by its ID"
)
async def get_transaction_by_id(
    transaction_id: int,
    session=Depends(get_session)
) -> Transaction:
    """
    Get transaction by ID.

    Args:
        transaction_id: Transaction ID
        session: Database session

    Returns:
        Transaction: Transaction object

    Raises:
        HTTPException: If transaction not found
    """
    transaction = TransactionService.get_transaction_by_id(transaction_id, session)
    if transaction is None:
        logger.warning(f"Transaction not found: ID {transaction_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction

# ============================================
# 4. ПОДТВЕРЖДЕНИЕ ТРАНЗАКЦИИ (АДМИН)
# ============================================
@transaction_route.post(
    '/{transaction_id}/approve',
    response_model=Transaction,
    summary="Approve Transaction",
    description="Approve a pending transaction"
)
async def approve_transaction(
    transaction_id: int,
    session=Depends(get_session)
) -> Transaction:
    """
    Approve a transaction.

    Args:
        transaction_id: Transaction ID
        session: Database session

    Returns:
        Transaction: Approved transaction

    Raises:
        HTTPException: If transaction not found or already processed
    """
    try:
        transaction = TransactionService.get_transaction_by_id(transaction_id, session)
        if transaction is None:
            logger.warning(f"Approve attempt for non-existent transaction: ID {transaction_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        approved_transaction = TransactionService.approve_transaction(transaction_id, session)
        logger.info(f"Transaction approved: ID {transaction_id}")
        return approved_transaction

    except ValueError as e:
        logger.warning(f"Transaction approval error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error approving transaction"
        )

@transaction_route.post(
    '/{transaction_id}/reject',
    response_model=Transaction,
    summary="Reject Transaction",
    description="Reject a pending transaction"
)
async def reject_transaction(
    transaction_id: int,
    session=Depends(get_session)
) -> Transaction:
    """
    Reject a transaction.

    Args:
        transaction_id: Transaction ID
        session: Database session

    Returns:
        Transaction: Rejected transaction

    Raises:
        HTTPException: If transaction not found or already processed
    """
    try:
        transaction = TransactionService.get_transaction_by_id(transaction_id, session)
        if transaction is None:
            logger.warning(f"Reject attempt for non-existent transaction: ID {transaction_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )

        rejected_transaction = TransactionService.reject_transaction(transaction_id, session)
        logger.info(f"Transaction rejected: ID {transaction_id}")
        return rejected_transaction

    except ValueError as e:
        logger.warning(f"Transaction rejection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error rejecting transaction"
        )

@transaction_route.get(
    '/all',
    response_model=List[Transaction],
    summary="Get All Transactions",
    description="Get all transactions (admin only)"
)
async def get_all_transactions(
    session=Depends(get_session)
) -> List[Transaction]:
    """
    Get all transactions.

    Args:
        session: Database session

    Returns:
        List[Transaction]: List of all transactions
    """
    try:
        transactions = TransactionService.get_all_transactions(session)
        logger.info(f"Retrieved {len(transactions)} transactions")
        return transactions
    except Exception as e:
        logger.error(f"Error retrieving transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving transactions"
        )

@transaction_route.get(
    '/pending/all',
    response_model=List[Transaction],
    summary="Get Pending Transactions",
    description="Get all pending transactions (admin only)"
)
async def get_pending_transactions(
    session=Depends(get_session)
) -> List[Transaction]:
    """
    Get all pending transactions.

    Args:
        session: Database session

    Returns:
        List[Transaction]: List of pending transactions
    """
    try:
        transactions = TransactionService.get_pending_transactions(session)
        logger.info(f"Retrieved {len(transactions)} pending transactions")
        return transactions
    except Exception as e:
        logger.error(f"Error retrieving pending transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving pending transactions"
        )