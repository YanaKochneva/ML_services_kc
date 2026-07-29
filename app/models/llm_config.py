from dataclasses import dataclass
from .base import BaseEntity

@dataclass
class LLMConfig(BaseEntity):
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
    name: str = "Qwen3-8B"
    version: str = "1.0"
    cost_per_request: int = 1
    description: str = "Language model for text generation"
    max_prompt_length: int = 4000
    is_active: bool = True
    
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