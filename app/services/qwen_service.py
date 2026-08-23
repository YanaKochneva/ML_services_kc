import logging
import os
import torch

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
try:
    import huggingface_hub.constants as _hf_constants
    _hf_constants.ENDPOINT = os.environ["HF_ENDPOINT"]
except Exception:
    pass

from typing import Dict, Any, List, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from models.llm_interface import LLMServiceInterface
from models.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class QwenService(LLMServiceInterface):
    def __init__(self, model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading {model_name} on {self.device}...")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto" if self.device == "cuda" else None,
            low_cpu_mem_usage=True
        )
        if self.device == "cpu":
            self.model = self.model.to("cpu")

        logger.info(f"{model_name} loaded successfully")

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

    def generate(self, data: Any, config: Optional[LLMConfig] = None) -> Dict[str, Any]:
        """
        Генерирует ответ на основе данных запроса и конфигурации.
        """
        if isinstance(data, str):
            prompt = data
        else:
            prompt = data.get('prompt', '')

        if self.device == "cpu":
            max_new_tokens = 96
        else:
            max_new_tokens = 256

        messages = [{"role": "user", "content": prompt}]

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        model_inputs = self.tokenizer([text], return_tensors="pt").to(self.model.device)

        generated_ids = self.model.generate(
            **model_inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):]
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True)

        return {
            "response": response,
            "model_name": config.name if config else self.model_name,
            "model_version": config.version if config else "v1.0",
            "tokens_used": len(output_ids),
            "finish_reason": "stop"
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


_qwen_service: Optional[QwenService] = None


def get_qwen_service() -> QwenService:
    global _qwen_service
    if _qwen_service is None:
        _qwen_service = QwenService()
    return _qwen_service