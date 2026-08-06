# routes/balance_route.py
from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.balance import Balance
from models.user import User
from services.crud import user as UserService
from typing import Dict
import logging

# Configure logging
logger = logging.getLogger(__name__)

balance_route = APIRouter()

@balance_route.get(
    '/user/{user_id}',
    response_model=Dict[str, float],
    summary="Get User Balance",
    description="Get the current balance of a specific user"
)
async def get_user_balance(
    user_id: int,
    session=Depends(get_session)
) -> Dict[str, float]:
    """
    Get user balance.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        dict: User balance in credits and rubles

    Raises:
        HTTPException: If user not found
    """
    # Проверяем, существует ли пользователь
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        logger.warning(f"Balance request for non-existent user: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    balance = user.balance
    if balance is None:
        logger.warning(f"Balance not found for user: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found for user"
        )

    logger.info(f"Balance retrieved for user ID {user_id}: {balance.credits} credits")
    return {
        "credits": float(balance.credits),
        "rubles": balance.to_rubles()
    }

@balance_route.post(
    '/user/{user_id}/deposit',
    response_model=Dict[str, float],
    summary="Deposit Credits",
    description="Deposit credits to user balance"
)
async def deposit_credits(
    user_id: int,
    deposit_data: Dict[str, int],
    session=Depends(get_session)
) -> Dict[str, float]:
    """
    Deposit credits to user balance.

    Args:
        user_id: User ID
        deposit_data: Dict with 'credits' field
        session: Database session

    Returns:
        dict: New balance

    Raises:
        HTTPException: If user not found or invalid amount
    """
    try:
        # Проверяем, существует ли пользователь
        user = UserService.get_user_by_id(user_id, session)
        if user is None:
            logger.warning(f"Deposit attempt for non-existent user: ID {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Получаем количество кредитов
        credits = deposit_data.get('credits')
        if credits is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'credits' field is required"
            )
        if credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credits amount must be positive"
            )

        # Пополняем баланс
        balance = user.balance
        if balance is None:
            logger.error(f"Balance not found for user ID {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Balance not found for user"
            )

        balance.deposit(credits)
        session.add(balance)
        session.commit()
        session.refresh(balance)

        logger.info(f"Deposited {credits} credits for user ID {user_id}. New balance: {balance.credits}")
        return {
            "message": "Balance deposited successfully",
            "credits": float(balance.credits),
            "rubles": balance.to_rubles()
        }

    except ValueError as e:
        logger.warning(f"Deposit validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error depositing credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error depositing credits"
        )

@balance_route.post(
    '/user/{user_id}/withdraw',
    response_model=Dict[str, float],
    summary="Withdraw Credits",
    description="Withdraw credits from user balance"
)
async def withdraw_credits(
    user_id: int,
    withdraw_data: Dict[str, int],
    session=Depends(get_session)
) -> Dict[str, float]:
    """
    Withdraw credits from user balance.

    Args:
        user_id: User ID
        withdraw_data: Dict with 'credits' field
        session: Database session

    Returns:
        dict: New balance

    Raises:
        HTTPException: If user not found or insufficient balance
    """
    try:
        # Проверяем, существует ли пользователь
        user = UserService.get_user_by_id(user_id, session)
        if user is None:
            logger.warning(f"Withdraw attempt for non-existent user: ID {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        credits = withdraw_data.get('credits')
        if credits is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'credits' field is required"
            )
        if credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credits amount must be positive"
            )

        balance = user.balance
        if balance is None:
            logger.error(f"Balance not found for user ID {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Balance not found for user"
            )

        if not balance.has_enough(credits):
            logger.warning(f"Insufficient balance for user ID {user_id}. Required: {credits}, Available: {balance.credits}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )

        balance.withdraw(credits)
        session.add(balance)
        session.commit()
        session.refresh(balance)

        logger.info(f"Withdrew {credits} credits from user ID {user_id}. New balance: {balance.credits}")
        return {
            "message": "Balance withdrawn successfully",
            "credits": float(balance.credits),
            "rubles": balance.to_rubles()
        }

    except ValueError as e:
        logger.warning(f"Withdraw validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error withdrawing credits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error withdrawing credits"
        )

@balance_route.post(
    '/user/{user_id}/check',
    response_model=Dict[str, bool],
    summary="Check Balance Sufficiency",
    description="Check if user has enough credits"
)
async def check_balance(
    user_id: int,
    check_data: Dict[str, int],
    session=Depends(get_session)
) -> Dict[str, bool]:
    """
    Check if user has enough credits.

    Args:
        user_id: User ID
        check_data: Dict with 'credits' field
        session: Database session

    Returns:
        dict: Whether user has enough credits

    Raises:
        HTTPException: If user not found
    """
    try:
        user = UserService.get_user_by_id(user_id, session)
        if user is None:
            logger.warning(f"Balance check for non-existent user: ID {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        credits = check_data.get('credits')
        if credits is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'credits' field is required"
            )
        if credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Credits amount must be positive"
            )

        balance = user.balance
        if balance is None:
            logger.error(f"Balance not found for user ID {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Balance not found for user"
            )

        has_enough = balance.has_enough(credits)
        logger.info(f"Balance check for user ID {user_id}: {credits} credits - {'Enough' if has_enough else 'Not enough'}")
        return {
            "has_enough": has_enough,
            "available": float(balance.credits),
            "required": credits
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error checking balance"
        )

@balance_route.post(
    '/convert/credits-to-rubles',
    response_model=Dict[str, float],
    summary="Convert Credits to Rubles",
    description="Convert credits to rubles"
)
async def convert_credits_to_rubles(
    convert_data: Dict[str, int]
) -> Dict[str, float]:
    """
    Convert credits to rubles.

    Args:
        convert_data: Dict with 'credits' field

    Returns:
        dict: Amount in rubles
    """
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
    """
    Convert rubles to credits.

    Args:
        convert_data: Dict with 'rubles' field

    Returns:
        dict: Amount in credits
    """
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