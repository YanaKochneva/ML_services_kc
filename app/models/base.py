from dataclasses import dataclass 
from abc import ABC, abstractmethod

@dataclass
class BaseEntity(ABC):
    """
    Абстрактный базовый класс для всех сущностей системы.
    Обеспечивает единый интерфейс для валидации и представления.
    """
    id: int
    
    @abstractmethod
    def validate(self) -> None:
        """Абстрактный метод валидации. Должен быть реализован в наследниках."""
        pass
    
    def __post_init__(self) -> None:
        """Автоматическая валидация после инициализации."""
        if not getattr(self.__class__, '__isabstractmethod__', False):
            self.validate()