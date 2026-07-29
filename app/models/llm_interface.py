from abc import abstractmethod, ABC
from typing import Dict, Any, List
from .llm_config import LLMConfig

class LLMServiceInterface(ABC):
    """
    Абстрактный интерфейс для LLM сервисов.
    """
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any], config: LLMConfig) -> List[str]:
        """
        Валидация входных данных с учетом конфигурации.
        """
        pass
    
    @abstractmethod
    def generate(self, data: Dict[str, Any], config: LLMConfig) -> Dict[str, Any]:
        """
        Генерация ответа LLM.
        """
        pass
    
    @abstractmethod
    def get_model_info(self, config: LLMConfig) -> Dict[str, Any]:
        """
        Получение информации о модели.
        """
        pass