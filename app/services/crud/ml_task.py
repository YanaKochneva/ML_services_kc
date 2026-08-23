# services/crud/ml_task.py
from sqlmodel import Session, select
from models.ml_task import MLTask
from models.user import User
from models.llm_config import LLMConfig
from typing import List, Optional, Dict, Any
from datetime import datetime

def create_ml_task(task: MLTask, session: Session) -> MLTask:
    """
    Создание новой ML задачи.
    
    Args:
        task: Задача для создания
        session: Сессия БД
    
    Returns:
        MLTask: Созданная задача
    
    Raises:
        ValueError: Если пользователь не найден или данные невалидны
    """
    user = session.get(User, task.user_id)
    if not user:
        raise ValueError(f"User with id {task.user_id} not found")
    
    if task.llm_config_id:
        config = session.get(LLMConfig, task.llm_config_id)
        if not config:
            raise ValueError(f"LLMConfig with id {task.llm_config_id} not found")
    
    task.validate()
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def get_all_ml_tasks(session: Session, status: Optional[str] = None) -> List[MLTask]:
    """
    Получение всех ML задач с возможной фильтрацией по статусу.
    
    Args:
        session: Сессия БД
        status: Статус для фильтрации (опционально)
    
    Returns:
        List[MLTask]: Список задач
    """
    query = select(MLTask)
    if status:
        query = query.where(MLTask.status == status)
    return session.exec(query).all()

def get_ml_task_by_id(task_id: int, session: Session) -> Optional[MLTask]:
    """
    Получение ML задачи по ID.
    
    Args:
        task_id: ID задачи
        session: Сессия БД
    
    Returns:
        Optional[MLTask]: Найденная задача или None
    """
    return session.get(MLTask, task_id)

def get_tasks_by_user(user_id: int, session: Session, status: Optional[str] = None) -> List[MLTask]:
    """
    Получение всех задач пользователя.
    
    Args:
        user_id: ID пользователя
        session: Сессия БД
        status: Статус для фильтрации (опционально)
    
    Returns:
        List[MLTask]: Список задач пользователя
    """
    query = select(MLTask).where(MLTask.user_id == user_id)
    if status:
        query = query.where(MLTask.status == status)
    return session.exec(query).all()

def get_tasks_by_config(config_id: int, session: Session) -> List[MLTask]:
    """
    Получение всех задач по конфигурации LLM.
    
    Args:
        config_id: ID конфигурации
        session: Сессия БД
    
    Returns:
        List[MLTask]: Список задач
    """
    return session.exec(
        select(MLTask).where(MLTask.llm_config_id == config_id)
    ).all()

def update_ml_task(task_id: int, update_data: dict, session: Session) -> Optional[MLTask]:
    """
    Обновление ML задачи.
    
    Args:
        task_id: ID задачи
        update_data: Данные для обновления
        session: Сессия БД
    
    Returns:
        Optional[MLTask]: Обновленная задача или None
    """
    task = session.get(MLTask, task_id)
    if not task:
        return None
    
    for key, value in update_data.items():
        if hasattr(task, key) and key not in ['id', 'user_id', 'created_at']:
            setattr(task, key, value)
    
    task.validate()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def update_task_status(task_id: int, status: str, session: Session) -> Optional[MLTask]:
    """
    Обновление статуса ML задачи.
    
    Args:
        task_id: ID задачи
        status: Новый статус
        session: Сессия БД
    
    Returns:
        Optional[MLTask]: Обновленная задача или None
    """
    task = session.get(MLTask, task_id)
    if not task:
        return None
    
    task.status = status
    if status in ['completed', 'failed']:
        task.completed_at = datetime.utcnow()
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def complete_ml_task(task_id: int, result: Dict[str, Any], session: Session) -> Optional[MLTask]:
    """
    Завершение ML задачи с результатом.
    
    Args:
        task_id: ID задачи
        result: Результат выполнения
        session: Сессия БД
    
    Returns:
        Optional[MLTask]: Завершенная задача или None
    """
    task = session.get(MLTask, task_id)
    if not task:
        return None
    
    task.complete(result)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def fail_ml_task(task_id: int, error: str, session: Session) -> Optional[MLTask]:
    """
    Отметка о провале ML задачи.
    
    Args:
        task_id: ID задачи
        error: Сообщение об ошибке
        session: Сессия БД
    
    Returns:
        Optional[MLTask]: Задача с ошибкой или None
    """
    task = session.get(MLTask, task_id)
    if not task:
        return None
    
    task.fail(error)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def add_validation_error_to_task(task_id: int, error: str, session: Session) -> Optional[MLTask]:
    """
    Добавление ошибки валидации к ML задаче.
    
    Args:
        task_id: ID задачи
        error: Ошибка валидации
        session: Сессия БД
    
    Returns:
        Optional[MLTask]: Задача с ошибкой валидации или None
    """
    task = session.get(MLTask, task_id)
    if not task:
        return None
    
    task.add_validation_error(error)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

def delete_ml_task(task_id: int, session: Session) -> bool:
    """
    Удаление ML задачи.
    
    Args:
        task_id: ID задачи
        session: Сессия БД
    
    Returns:
        bool: True если задача удалена
    """
    task = session.get(MLTask, task_id)
    if not task:
        return False
    
    session.delete(task)
    session.commit()
    return True

def get_pending_tasks(session: Session) -> List[MLTask]:
    """
    Получение всех задач в статусе PENDING.
    
    Args:
        session: Сессия БД
    
    Returns:
        List[MLTask]: Список задач в ожидании
    """
    return session.exec(
        select(MLTask).where(MLTask.status == "pending")
    ).all()

def get_tasks_by_statuses(session: Session, statuses: List[str]) -> List[MLTask]:
    """
    Получение задач по списку статусов.
    
    Args:
        session: Сессия БД
        statuses: Список статусов
    
    Returns:
        List[MLTask]: Список задач
    """
    return session.exec(
        select(MLTask).where(MLTask.status.in_(statuses))
    ).all()

def get_user_task_count(user_id: int, session: Session, status: Optional[str] = None) -> int:
    """
    Получение количества задач пользователя.
    
    Args:
        user_id: ID пользователя
        session: Сессия БД
        status: Статус для фильтрации (опционально)
    
    Returns:
        int: Количество задач
    """
    query = select(MLTask).where(MLTask.user_id == user_id)
    if status:
        query = query.where(MLTask.status == status)
    return len(session.exec(query).all())