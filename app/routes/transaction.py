from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.transaction import Transaction
from models.user import User
from services.crud import transaction as TransactionService
from services.crud import user as UserService
from services.auth.auth import get_current_user, get_current_active_admin
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)
transaction_route = APIRouter()

@transaction_route.post(
    '/create',
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED,
    summary="Create Transaction"
)
async def create_transaction(
    data: Transaction,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> Transaction:
    try:
        transaction = Transaction(
            user_id=current_user.id, 
            amount=data.amount,
            transaction_type=data.transaction_type,
            description=data.description or "",
            status="pending"
        )
        created = TransactionService.create_transaction(transaction, session)
        logger.info(f"Transaction created: ID {created.id}, User ID: {current_user.id}")
        return created
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        raise HTTPException(500, "Internal server error")

@transaction_route.get(
    '/me',
    response_model=List[Transaction],
    summary="Get my transactions"
)
async def get_my_transactions(
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> List[Transaction]:
    return TransactionService.get_transactions_by_user_id(current_user.id, session)

@transaction_route.get(
    '/user/{user_id}',
    response_model=List[Transaction],
    summary="Get user transactions (admin only)"
)
async def get_user_transactions(
    user_id: int,
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> List[Transaction]:
    user = UserService.get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(404, "User not found")
    return TransactionService.get_transactions_by_user_id(user_id, session)

@transaction_route.get(
    '/{transaction_id}',
    response_model=Transaction,
    summary="Get transaction by ID"
)
async def get_transaction_by_id(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> Transaction:
    transaction = TransactionService.get_transaction_by_id(transaction_id, session)
    if not transaction:
        raise HTTPException(404, "Transaction not found")
    if current_user.role != "admin" and transaction.user_id != current_user.id:
        raise HTTPException(403, "Not allowed")
    return transaction

@transaction_route.post(
    '/{transaction_id}/approve',
    response_model=Transaction,
    summary="Approve transaction (admin only)"
)
async def approve_transaction(
    transaction_id: int,
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> Transaction:
    try:
        approved = TransactionService.approve_transaction(transaction_id, session)
        if not approved:
            raise HTTPException(404, "Transaction not found")
        return approved
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error approving transaction: {str(e)}")
        raise HTTPException(500, "Internal server error")

@transaction_route.post(
    '/{transaction_id}/reject',
    response_model=Transaction,
    summary="Reject transaction (admin only)"
)
async def reject_transaction(
    transaction_id: int,
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> Transaction:
    try:
        rejected = TransactionService.reject_transaction(transaction_id, session)
        if not rejected:
            raise HTTPException(404, "Transaction not found")
        return rejected
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error rejecting transaction: {str(e)}")
        raise HTTPException(500, "Internal server error")

@transaction_route.get(
    '/all',
    response_model=List[Transaction],
    summary="Get all transactions (admin only)"
)
async def get_all_transactions(
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> List[Transaction]:
    return TransactionService.get_all_transactions(session)

@transaction_route.get(
    '/pending/all',
    response_model=List[Transaction],
    summary="Get pending transactions (admin only)"
)
async def get_pending_transactions(
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> List[Transaction]:
    return TransactionService.get_pending_transactions(session)