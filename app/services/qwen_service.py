import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logger = logging.getLogger(__name__)

class QwenService:
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

    def generate(self, prompt: str, max_new_tokens: int = 2048) -> dict:
        """
        Генерирует ответ на основе prompt.
        Возвращает словарь с response и метаданными.
        """
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
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        output_ids = generated_ids[0][len(model_inputs.input_ids[0]):]
        response = self.tokenizer.decode(output_ids, skip_special_tokens=True)
        
        return {
            "response": response,
            "model_name": self.model_name,
            "tokens_used": len(output_ids)
        }

_qwen_service = None

def get_qwen_service():
    global _qwen_service
    if _qwen_service is None:
        _qwen_service = QwenService()
    return _qwen_service