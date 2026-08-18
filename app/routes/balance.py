# routes/balance_route.py
from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.balance import Balance
from models.user import User
from models.transaction import Transaction
from models.enums import TransactionType
from services.crud import user as UserService
from typing import Dict, Any
import logging
from decimal import Decimal
from services.auth.auth import get_current_user, get_current_active_admin

# Configure logging
logger = logging.getLogger(__name__)

balance_route = APIRouter()

@balance_route.get(
    '/me',
    response_model=Dict[str, float],
    summary="Get user balance"
)
async def get_user_balance(
    current_user: User = Depends(get_current_user)
) -> Dict[str, float]:
    balance = current_user.balance
    return {
        "credits": float(balance.credits),
        "rubles": balance.to_rubles()
    }

@balance_route.post(
    '/me/deposit',
    response_model=Dict[str, Any],
    summary="Deposit credits to user balance"
)
async def deposit_my_credits(
    deposit_data: Dict[str, int],
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> Dict[str, Any]:
    try:
        credits = deposit_data.get('credits')
        if credits is None or credits <= 0:
            raise HTTPException(400, "Credits must be positive")
        current_user.balance.deposit(credits)
        session.add(current_user.balance)

        transaction = Transaction(
            user_id=current_user.id,
            amount=Balance.credits_to_rub(Decimal(credits)),
            transaction_type=TransactionType.DEPOSIT,
            description="Balance deposit",
            status="approved"
        )
        session.add(transaction)

        session.commit()
        session.refresh(current_user.balance)
        return {
            "message": "Balance deposited successfully",
            "credits": float(current_user.balance.credits),
            "rubles": current_user.balance.to_rubles()
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error depositing: {str(e)}")
        raise HTTPException(500, "Internal server error")

@balance_route.post(
    '/me/withdraw',
    response_model=Dict[str, Any],
    summary="Withdraw credits from user balance"
)
async def withdraw_my_credits(
    withdraw_data: Dict[str, int],
    current_user: User = Depends(get_current_user),
    session=Depends(get_session)
) -> Dict[str, float]:
    try:
        credits = withdraw_data.get('credits')
        if credits is None or credits <= 0:
            raise HTTPException(400, "Credits must be positive")
        if not current_user.balance.has_enough(credits):
            raise HTTPException(400, "Insufficient balance")
        current_user.balance.withdraw(credits)
        session.add(current_user.balance)
        session.commit()
        session.refresh(current_user.balance)
        return {
            "message": "Balance withdrawn successfully",
            "credits": float(current_user.balance.credits),
            "rubles": current_user.balance.to_rubles()
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error withdrawing: {str(e)}")
        raise HTTPException(500, "Internal server error")

@balance_route.post(
    '/me/check',
    response_model=Dict[str, bool],
    summary="Check if user has enough credits"
)
async def check_my_balance(
    check_data: Dict[str, int],
    current_user: User = Depends(get_current_user)
) -> Dict[str, bool]:
    try:
        credits = check_data.get('credits')
        if credits is None or credits <= 0:
            raise HTTPException(400, "Credits must be positive")
        has_enough = current_user.balance.has_enough(credits)
        return {
            "has_enough": has_enough,
            "available": float(current_user.balance.credits),
            "required": credits
        }
    except Exception as e:
        logger.error(f"Error checking balance: {str(e)}")
        raise HTTPException(500, "Internal server error")

@balance_route.get(
    '/user/{user_id}',
    response_model=Dict[str, float],
    summary="Get user balance (admin only)"
)
async def get_user_balance(
    user_id: int,
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> Dict[str, float]:
    user = UserService.get_user_by_id(user_id, session)
    if not user:
        raise HTTPException(404, "User not found")
    balance = user.balance
    if not balance:
        raise HTTPException(404, "Balance not found")
    return {
        "credits": float(balance.credits),
        "rubles": balance.to_rubles()
    }

@balance_route.post(
    '/user/{user_id}/deposit',
    response_model=Dict[str, Any],
    summary="Deposit credits to user (admin only)"
)
async def deposit_user_credits(
    user_id: int,
    deposit_data: Dict[str, int],
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> Dict[str, float]:
    try:
        user = UserService.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(404, "User not found")
        credits = deposit_data.get('credits')
        if credits is None or credits <= 0:
            raise HTTPException(400, "Credits must be positive")
        user.balance.deposit(credits)
        session.add(user.balance)
        session.commit()
        session.refresh(user.balance)
        return {
            "message": "Balance deposited successfully",
            "credits": float(user.balance.credits),
            "rubles": user.balance.to_rubles()
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error depositing: {str(e)}")
        raise HTTPException(500, "Internal server error")

@balance_route.post(
    '/user/{user_id}/withdraw',
    response_model=Dict[str, Any],
    summary="Withdraw credits from user (admin only)"
)
async def withdraw_user_credits(
    user_id: int,
    withdraw_data: Dict[str, int],
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> Dict[str, float]:
    try:
        user = UserService.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(404, "User not found")
        credits = withdraw_data.get('credits')
        if credits is None or credits <= 0:
            raise HTTPException(400, "Credits must be positive")
        if not user.balance.has_enough(credits):
            raise HTTPException(400, "Insufficient balance")
        user.balance.withdraw(credits)
        session.add(user.balance)
        session.commit()
        session.refresh(user.balance)
        return {
            "message": "Balance withdrawn successfully",
            "credits": float(user.balance.credits),
            "rubles": user.balance.to_rubles()
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"Error withdrawing: {str(e)}")
        raise HTTPException(500, "Internal server error")

@balance_route.post(
    '/user/{user_id}/check',
    response_model=Dict[str, bool],
    summary="Check user balance (admin only)"
)
async def check_user_balance(
    user_id: int,
    check_data: Dict[str, int],
    admin: User = Depends(get_current_active_admin),
    session=Depends(get_session)
) -> Dict[str, bool]:
    try:
        user = UserService.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(404, "User not found")
        credits = check_data.get('credits')
        if credits is None or credits <= 0:
            raise HTTPException(400, "Credits must be positive")
        has_enough = user.balance.has_enough(credits)
        return {
            "has_enough": has_enough,
            "available": float(user.balance.credits),
            "required": credits
        }
    except Exception as e:
        logger.error(f"Error checking balance: {str(e)}")
        raise HTTPException(500, "Internal server error")

@balance_route.post(
    '/convert/credits-to-rubles',
    response_model=Dict[str, float],
    summary="Convert Credits to Rubles",
    description="Convert credits to rubles"
)
async def convert_credits_to_rubles(
    convert_data: Dict[str, int]
) -> Dict[str, float]:
    try:
        credits = convert_data.get('credits')
        if credits is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'credits' field is required"
            )
        if credits < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credits amount cannot be negative"
            )

        rubles = credits * Balance.CREDIT_PRICE_RUB
        logger.info(f"Converted {credits} credits to {rubles} rubles")
        return {
            "credits": credits,
            "rubles": rubles
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error converting credits"
        )

@balance_route.post(
    '/convert/rubles-to-credits',
    response_model=Dict[str, float],
    summary="Convert Rubles to Credits",
    description="Convert rubles to credits"
)
async def convert_rubles_to_credits(
    convert_data: Dict[str, float]
) -> Dict[str, float]:
    try:
        rubles = convert_data.get('rubles')
        if rubles is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'rubles' field is required"
            )
        if rubles <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rubles amount must be positive"
            )

        credits = Balance.rub_to_credits(rubles)
        logger.info(f"Converted {rubles} rubles to {credits} credits")
        return {
            "rubles": rubles,
            "credits": credits
        }

    except ValueError as e:
        logger.warning(f"Conversion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting rubles: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error converting rubles"
        )