from typing import List, Dict, Any
from .llm_interface import LLMServiceInterface
from .llm_config import LLMConfig

class DefaultLLMService(LLMServiceInterface):
    """
    Реализация LLM сервиса.
    """
    
    def validate_data(self, data: Dict[str, Any], config: LLMConfig) -> List[str]:
        """Валидация данных для LLM."""
        errors = []
        
        if 'prompt' not in data:
            errors.append("Missing 'prompt' field")
        elif not isinstance(data['prompt'], str):
            errors.append("'prompt' must be a string")
        elif len(data['prompt'].strip()) == 0:
            errors.append("'prompt' cannot be empty")
        
        if 'prompt' in data and isinstance(data['prompt'], str):
            if len(data['prompt']) > config.max_prompt_length:
                errors.append(f"'prompt' exceeds maximum length of {config.max_prompt_length} characters")
        
        return errors
    
    def generate(self, data: Dict[str, Any], config: LLMConfig) -> Dict[str, Any]:
        """Генерация ответа LLM."""
        prompt = data.get('prompt', '')
        
        response = f"[{config.name}] Ответ на ваш запрос: '{prompt[:50]}...'"
        
        return {
            'response': response,
            'model_name': config.name,
            'model_version': config.version,
            'tokens_used': len(prompt.split()) + len(response.split()),
            'finish_reason': 'stop'
        }
    
    def get_model_info(self, config: LLMConfig) -> Dict[str, Any]:
        """Получение информации о модели."""
        return {
            'name': config.name,
            'version': config.version,
            'description': config.description,
            'max_prompt_length': config.max_prompt_length,
            'cost_per_request': config.cost_per_request,
            'capabilities': ['text_generation', 'chat_completion']
        }