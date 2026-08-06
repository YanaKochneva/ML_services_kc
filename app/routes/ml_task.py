# routes/ml_task_route.py
from fastapi import APIRouter, HTTPException, status, Depends
from database.database import get_session
from models.ml_task import MLTask
from models.user import User
from models.llm_config import LLMConfig
from services.crud import ml_task as MLTaskService
from services.crud import user as UserService
from services.crud import llm_config as LLMConfigService
from typing import List, Dict, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)

ml_task_route = APIRouter()

@ml_task_route.post(
    '/create',
    response_model=MLTask,
    status_code=status.HTTP_201_CREATED,
    summary="Create ML Task",
    description="Create a new ML task for text generation"
)
async def create_ml_task(
    data: MLTask,
    session=Depends(get_session)
) -> MLTask:
    """
    Create new ML task.

    Args:
        data: MLTask data (user_id, llm_config_id, input_data, cost)
        session: Database session

    Returns:
        MLTask: Created ML task

    Raises:
        HTTPException: If user or config not found, or validation fails
    """
    try:
        # Проверяем, существует ли пользователь
        user = UserService.get_user_by_id(data.user_id, session)
        if user is None:
            logger.warning(f"ML task creation attempt for non-existent user: ID {data.user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Проверяем, существует ли конфигурация LLM
        if data.llm_config_id:
            config = LLMConfigService.get_llm_config_by_id(data.llm_config_id, session)
            if config is None:
                logger.warning(f"ML task creation attempt for non-existent config: ID {data.llm_config_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="LLM config not found"
                )

        task = MLTask(
            user_id=data.user_id,
            llm_config_id=data.llm_config_id,
            input_data=data.input_data,
            cost=data.cost,
            status="PENDING"
        )
        
        created_task = MLTaskService.create_ml_task(task, session)
        logger.info(f"ML task created: ID {created_task.id}, User ID: {data.user_id}")
        return created_task

    except ValueError as e:
        logger.warning(f"ML task validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ML task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating ML task"
        )

@ml_task_route.get(
    '/all',
    response_model=List[MLTask],
    summary="Get All ML Tasks",
    description="Get all ML tasks"
)
async def get_all_ml_tasks(
    session=Depends(get_session)
) -> List[MLTask]:
    """
    Get all ML tasks.

    Args:
        session: Database session

    Returns:
        List[MLTask]: List of all ML tasks
    """
    try:
        tasks = MLTaskService.get_all_ml_tasks(session)
        logger.info(f"Retrieved {len(tasks)} ML tasks")
        return tasks
    except Exception as e:
        logger.error(f"Error retrieving ML tasks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving ML tasks"
        )

@ml_task_route.get(
    '/user/{user_id}',
    response_model=List[MLTask],
    summary="Get ML Tasks by User",
    description="Get all ML tasks for a specific user"
)
async def get_user_ml_tasks(
    user_id: int,
    session=Depends(get_session)
) -> List[MLTask]:
    """
    Get all ML tasks for a user.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        List[MLTask]: List of user's ML tasks

    Raises:
        HTTPException: If user not found
    """
    # Проверяем, существует ли пользователь
    user = UserService.get_user_by_id(user_id, session)
    if user is None:
        logger.warning(f"Get ML tasks attempt for non-existent user: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    tasks = MLTaskService.get_tasks_by_user(user_id, session)
    logger.info(f"Retrieved {len(tasks)} ML tasks for user ID {user_id}")
    return tasks

@ml_task_route.get(
    '/status/{status}',
    response_model=List[MLTask],
    summary="Get ML Tasks by Status",
    description="Get all ML tasks with a specific status"
)
async def get_ml_tasks_by_status(
    status: str,
    session=Depends(get_session)
) -> List[MLTask]:
    """
    Get ML tasks by status.

    Args:
        status: Task status (PENDING, PROCESSING, COMPLETED, FAILED, VALIDATION_ERROR)
        session: Database session

    Returns:
        List[MLTask]: List of tasks with given status
    """
    try:
        tasks = MLTaskService.get_all_ml_tasks(session, status=status)
        logger.info(f"Retrieved {len(tasks)} ML tasks with status: {status}")
        return tasks
    except Exception as e:
        logger.error(f"Error retrieving ML tasks by status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving ML tasks"
        )

@ml_task_route.get(
    '/{task_id}',
    response_model=MLTask,
    summary="Get ML Task by ID",
    description="Get a specific ML task by its ID"
)
async def get_ml_task_by_id(
    task_id: int,
    session=Depends(get_session)
) -> MLTask:
    """
    Get ML task by ID.

    Args:
        task_id: Task ID
        session: Database session

    Returns:
        MLTask: ML task object

    Raises:
        HTTPException: If task not found
    """
    task = MLTaskService.get_ml_task_by_id(task_id, session)
    if task is None:
        logger.warning(f"ML task not found: ID {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ML task not found"
        )
    return task


@ml_task_route.put(
    '/{task_id}/status',
    response_model=MLTask,
    summary="Update Task Status",
    description="Update the status of a specific ML task"
)
async def update_task_status(
    task_id: int,
    status_data: Dict[str, str],
    session=Depends(get_session)
) -> MLTask:
    """
    Update task status.

    Args:
        task_id: Task ID
        status_data: Dict with 'status' field (PENDING, PROCESSING, COMPLETED, FAILED)
        session: Database session

    Returns:
        MLTask: Updated task

    Raises:
        HTTPException: If task not found or invalid status
    """
    try:
        new_status = status_data.get('status')
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status is required"
            )

        task = MLTaskService.update_task_status(task_id, new_status, session)
        if task is None:
            logger.warning(f"Update status attempt for non-existent task: ID {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ML task not found"
            )

        logger.info(f"Task status updated: ID {task_id}, New status: {new_status}")
        return task

    except ValueError as e:
        logger.warning(f"Invalid status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating task status"
        )

@ml_task_route.post(
    '/{task_id}/complete',
    response_model=MLTask,
    summary="Complete ML Task",
    description="Complete a task with output result"
)
async def complete_ml_task(
    task_id: int,
    result_data: Dict[str, Any],
    session=Depends(get_session)
) -> MLTask:
    """
    Complete a task with result.

    Args:
        task_id: Task ID
        result_data: Result data (response, tokens_used, etc.)
        session: Database session

    Returns:
        MLTask: Completed task

    Raises:
        HTTPException: If task not found
    """
    try:
        task = MLTaskService.complete_ml_task(task_id, result_data, session)
        if task is None:
            logger.warning(f"Complete attempt for non-existent task: ID {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ML task not found"
            )

        logger.info(f"Task completed: ID {task_id}")
        return task

    except ValueError as e:
        logger.warning(f"Task completion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error completing task"
        )

@ml_task_route.post(
    '/{task_id}/fail',
    response_model=MLTask,
    summary="Fail ML Task",
    description="Mark a task as failed with error message"
)
async def fail_ml_task(
    task_id: int,
    error_data: Dict[str, str],
    session=Depends(get_session)
) -> MLTask:
    """
    Fail a task with error message.

    Args:
        task_id: Task ID
        error_data: Dict with 'error' field
        session: Database session

    Returns:
        MLTask: Failed task

    Raises:
        HTTPException: If task not found
    """
    try:
        error = error_data.get('error', 'Unknown error')
        task = MLTaskService.fail_ml_task(task_id, error, session)
        if task is None:
            logger.warning(f"Fail attempt for non-existent task: ID {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ML task not found"
            )

        logger.info(f"Task marked as failed: ID {task_id}")
        return task

    except ValueError as e:
        logger.warning(f"Task fail error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error failing task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error failing task"
        )

@ml_task_route.post(
    '/{task_id}/validation_error',
    response_model=MLTask,
    summary="Add Validation Error",
    description="Add a validation error to a task"
)
async def add_validation_error(
    task_id: int,
    error_data: Dict[str, str],
    session=Depends(get_session)
) -> MLTask:
    """
    Add validation error to a task.

    Args:
        task_id: Task ID
        error_data: Dict with 'error' field
        session: Database session

    Returns:
        MLTask: Task with validation error

    Raises:
        HTTPException: If task not found
    """
    try:
        error = error_data.get('error', 'Validation error')
        task = MLTaskService.add_validation_error_to_task(task_id, error, session)
        if task is None:
            logger.warning(f"Validation error attempt for non-existent task: ID {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ML task not found"
            )

        logger.info(f"Validation error added to task: ID {task_id}")
        return task

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error adding validation error"
        )

@ml_task_route.delete(
    '/{task_id}',
    response_model=Dict[str, str],
    summary="Delete ML Task",
    description="Delete a specific ML task by its ID"
)
async def delete_ml_task(
    task_id: int,
    session=Depends(get_session)
) -> Dict[str, str]:
    """
    Delete ML task by ID.

    Args:
        task_id: Task ID
        session: Database session

    Returns:
        dict: Success message

    Raises:
        HTTPException: If task not found
    """
    try:
        task = MLTaskService.get_ml_task_by_id(task_id, session)
        if task is None:
            logger.warning(f"Delete attempt for non-existent task: ID {task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ML task not found"
            )

        MLTaskService.delete_ml_task(task_id, session)
        logger.info(f"ML task deleted: ID {task_id}")
        return {"message": "ML task successfully deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ML task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting ML task"
        )