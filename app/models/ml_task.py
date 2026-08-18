from dataclasses import dataclass, field
from .base import BaseEntity
from typing import List, Optional, Dict, Any
from .enums import TaskStatus
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from decimal import Decimal

if TYPE_CHECKING:
    from .user import User
    from .llm_config import LLMConfig

@dataclass
class MLTask(SQLModel, table=True):
    """
    Класс задачи для LLM сервиса.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        input_data (Dict[str, Any]): Запрос к LLM
        output_data (Optional[Dict[str, Any]]): Результат генерации
        status (str): Статус задачи
        cost (Decimal): Стоимость выполнения
        created_at (datetime): Дата создания
        completed_at (Optional[datetime]): Дата завершения
        error_message (Optional[str]): Сообщение об ошибке
        validation_errors (List[str]): Ошибки валидации данных
        user (User): Связанный пользователь
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    llm_config_id: Optional[int] = Field(foreign_key="llm_configs.id")
    input_data: Dict[str, Any] = Field(sa_column=Column(JSON))
    output_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    status: str = Field(default=TaskStatus.PENDING.value, max_length=20)
    cost: Decimal = Field(default=0, max_digits=10, decimal_places=2)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
    error_message: Optional[str] = Field(default=None, max_length=500)
    validation_errors: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )

    user: "User" = Relationship(back_populates="ml_tasks")
    llm_config: "LLMConfig" = Relationship(back_populates="ml_tasks", sa_relationship_kwargs={"lazy": "selectin"})

    
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
        self.status = TaskStatus.COMPLETED.value
        self.output_data = result
        self.completed_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """Отметка о провале задачи."""
        self.status = TaskStatus.FAILED.value
        self.error_message = error
        self.completed_at = datetime.now()
    
    def add_validation_error(self, error: str) -> None:
        """Добавление ошибки валидации."""
        self.validation_errors.append(error)
        self.status = TaskStatus.VALIDATION_ERROR.value
