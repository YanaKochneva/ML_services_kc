from dataclasses import dataclass
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

if TYPE_CHECKING:
    from .ml_task import MLTask

@dataclass
class LLMConfig(SQLModel, table=True):
    """
    Конфигурация LLM модели.
    
    Attributes:
        name: Название модели
        version: Версия модели
        cost_per_request: Стоимость одного запроса в кредитах
        description: Описание модели
        max_prompt_length: Максимальная длина запроса
        is_active: Доступна ли модель для использования
    """
    __tablename__ = "llm_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(
        default="Qwen3-8B",
        max_length=100
    )
    version: str = Field(
        default="1.0",
        max_length=20
    )
    cost_per_request: int = Field(
        default=1
    )
    description: str = Field(
        default="Language model for text generation",
        max_length=500
    )
    max_prompt_length: int = Field(
        default=4000
    )
    is_active: bool = Field(
        default=True,
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )
    
    # Связь с задачами (если нужно)
    ml_tasks: List["MLTask"] = Relationship(
        back_populates="llm_config",
        sa_relationship_kwargs={
            "lazy": "selectin"
        }
    )
    
    def validate(self) -> None:
        """Валидация конфигурации."""
        if not self.name:
            raise ValueError("Model name is required")
        if self.cost_per_request < 1 or self.cost_per_request > 3:
            raise ValueError("Cost per request must be between 1 and 3 credits")
        if not self.version:
            raise ValueError("Version is required")
        if self.max_prompt_length <= 0:
            raise ValueError("Max prompt length must be positive")