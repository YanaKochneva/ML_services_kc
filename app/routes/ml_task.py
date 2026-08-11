from fastapi import APIRouter, HTTPException, status, Depends, Query
from database.database import get_session
from models.ml_task import MLTask
from models.user import User
from models.balance import Balance
from models.llm_config import LLMConfig
from services.crud import ml_task as MLTaskService
from services.crud import user as UserService
from services.crud import llm_config as LLMConfigService
from models.default_llm import DefaultLLMService
from typing import List, Dict, Any
from decimal import Decimal
from sqlmodel import Session, select
from models.enums import TaskStatus, TransactionType
from models.transaction import Transaction
import logging
from datetime import datetime
from services.auth.auth import get_current_user, get_current_active_admin
from typing import Optional
from services.rm import send_task

# Configure logging
logger = logging.getLogger(__name__)

ml_task_route = APIRouter()

@ml_task_route.post(
    '/create',
    response_model=MLTask,
    status_code=status.HTTP_201_CREATED,
    summary="Create and execute ML Task",
    description="Create a new ML task, validate input, execute LLM, charge credits."
)
async def create_ml_task(
    data: MLTask,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> MLTask:
    """
    Создание и выполнение ML задачи.
    """
    try:
        user = current_user 
        if user is None:
            logger.warning(f"ML task creation attempt for non-existent user: ID {data.user_id}")
            raise HTTPException(status_code=404, detail="User not found")

        if not data.llm_config_id:
            raise HTTPException(status_code=400, detail="llm_config_id is required")
        config = LLMConfigService.get_llm_config_by_id(data.llm_config_id, session)
        if not config:
            raise HTTPException(status_code=404, detail="LLM config not found")
        if not config.is_active:
            raise HTTPException(status_code=400, detail="LLM config is not active")

        cost_credits = config.cost_per_request
        cost_rub = Balance.credits_to_rub(Decimal(cost_credits))

        if not user.balance.has_enough(cost_credits):
            raise HTTPException(status_code=400, detail="Insufficient balance")

        llm_service = DefaultLLMService()  
        validation_errors = llm_service.validate_data(data.input_data, config)
        if validation_errors:
            task = MLTask(
                user_id=user.id,
                llm_config_id=config.id,
                input_data=data.input_data,
                cost=cost_credits,
                status=TaskStatus.VALIDATION_ERROR.value,
                validation_errors=validation_errors
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            logger.warning(f"Validation errors for task {task.id}: {validation_errors}")
            return task

        task = MLTask(
            user_id=user.id,
            llm_config_id=config.id,
            input_data=data.input_data,
            cost=cost_credits,
            status=TaskStatus.PROCESSING.value
        )
        session.add(task)
        session.flush()   

        try:
            result = llm_service.generate(data.input_data, config)
        except Exception as e:
            task.status = TaskStatus.FAILED.value
            task.error_message = str(e)
            session.add(task)
            session.commit()
            logger.error(f"LLM generation failed for task {task.id}: {e}")
            return task

        task.status = TaskStatus.COMPLETED.value
        task.output_data = result
        task.completed_at = datetime.utcnow()

        user.balance.withdraw(cost_credits)

        transaction = Transaction(
            user_id=user.id,
            amount=cost_rub,
            transaction_type=TransactionType.WITHDRAW,
            description=f"Payment for ML task #{task.id}",
            status="approved"
        )
        session.add(transaction)

        session.add(task)
        session.add(user.balance)
        session.commit()
        session.refresh(task)

        logger.info(f"ML task {task.id} completed, charged {cost_credits} credits")
        return task

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating ML task: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@ml_task_route.get('/')
async def get_ml_tasks(
    user_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> List[MLTask]:
    if current_user.role != "admin":
        if user_id is not None and user_id != current_user.id:
            raise HTTPException(403, "Not allowed")
        user_id = current_user.id
    tasks = MLTaskService.get_all_ml_tasks(session, status=status)
    if user_id is not None:
        tasks = [t for t in tasks if t.user_id == user_id]
    return tasks


@ml_task_route.get('/{task_id}')
async def get_ml_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_user), 
    session=Depends(get_session)
) -> MLTask:
    task = MLTaskService.get_ml_task_by_id(task_id, session)
    if task is None:
        raise HTTPException(404, "ML task not found")
    # Проверка прав
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(403, "Not allowed to view this task")
    return task

@ml_task_route.delete('/{task_id}')
async def delete_ml_task(
    task_id: int,
    current_user: User = Depends(get_current_user),  
    session=Depends(get_session)
) -> Dict[str, str]:
    task = MLTaskService.get_ml_task_by_id(task_id, session)
    if task is None:
        raise HTTPException(404, "ML task not found")
    if current_user.role != "admin" and task.user_id != current_user.id:
        raise HTTPException(403, "Not allowed to delete this task")
    MLTaskService.delete_ml_task(task_id, session)
    return {"message": "ML task successfully deleted"}

@ml_task_route.post('/predict', response_model=Dict[str, str])
async def predict(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    features = request.get('features')
    model_name = request.get('model', 'Qwen2.5-1.5B-Instruct') 

    if not features or 'prompt' not in features:
        raise HTTPException(400, "Missing 'prompt' in features")

    llm_config = session.exec(
        select(LLMConfig).where(LLMConfig.name == model_name, LLMConfig.is_active == True)
    ).first()
    if not llm_config:
        raise HTTPException(404, f"LLM config '{model_name}' not found or inactive")

    cost = llm_config.cost_per_request
    if not current_user.balance.has_enough(cost):
        raise HTTPException(400, "Insufficient balance")

    task = MLTask(
        user_id=current_user.id,
        llm_config_id=llm_config.id,
        input_data=features,
        status=TaskStatus.PENDING.value,
        cost=cost,
        created_at=datetime.utcnow()
    )
    session.add(task)
    session.commit()
    session.refresh(task)

    message = {
        "task_id": str(task.id),
        "features": features,
        "llm_config_id": llm_config.id,
        "timestamp": datetime.utcnow().isoformat()
    }
    send_task(message)

    return {"task_id": str(task.id)}