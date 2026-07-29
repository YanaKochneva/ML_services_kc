from dataclasses import dataclass, field
from .base import BaseEntity
from typing import List, Optional, Dict, Any
from .enums import TaskStatus
from datetime import datetime

@dataclass
class MLTask(BaseEntity):
    """
    Класс задачи для LLM сервиса.
    
    Attributes:
        id: Уникальный идентификатор
        user_id: ID пользователя
        input_data: Запрос к LLM
        output_data: Результат генерации
        status: Статус задачи
        cost: Стоимость выполнения
        created_at: Дата создания
        completed_at: Дата завершения
        error_message: Сообщение об ошибке
        validation_errors: Ошибки валидации данных
    """
    user_id: int
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.PENDING
    cost: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Валидация ML задачи."""
        if self.user_id <= 0:
            raise ValueError("Invalid user ID")
        if not self.input_data:
            raise ValueError("Input data is required")
        if 'prompt' not in self.input_data:
            raise ValueError("Prompt is required")
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Завершение задачи с результатом."""
        self.status = TaskStatus.COMPLETED
        self.output_data = result
        self.completed_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """Отметка о провале задачи."""
        self.status = TaskStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now()
    
    def add_validation_error(self, error: str) -> None:
        """Добавление ошибки валидации."""
        self.validation_errors.append(error)
        self.status = TaskStatus.VALIDATION_ERROR