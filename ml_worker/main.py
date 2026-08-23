import pika
import json
import logging
import os
import threading
from datetime import datetime
from decimal import Decimal
from sqlmodel import Session
from database.database import engine  # без app.
from models.ml_task import MLTask
from models.enums import TaskStatus, TransactionType
from models.transaction import Transaction
from models.llm_config import LLMConfig
from models.balance import Balance
from services.qwen_service import QwenService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'rmuser')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASSWORD', 'rmpassword')
QUEUE_NAME = 'ml_task_queue'
WORKER_ID = os.getenv('WORKER_ID', 'worker-1')

# Ленивая инициализация LLM: веса модели (~3.1 ГБ) могут быть ещё не докачаны,
# поэтому воркер НЕ должен падать при старте. Модель загружается при первом
# поступлении задачи (и в фоне при необходимости докачки).
_llm_service = None
_llm_lock = threading.Lock()
MODEL_NOT_READY_MSG = ("Модель ещё не загружена (веса ~3.1 ГБ докачиваются в фоне). "
                       "Подождите завершения загрузки и отправьте запрос повторно.")
MODEL_CACHE_PATH = os.path.expanduser(
    "~/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/snapshots"
)


def is_model_ready() -> bool:
    """Проверяет, что файл весов model.safetensors уже докачан в кэш."""
    if not os.path.isdir(MODEL_CACHE_PATH):
        return False
    for rev in os.listdir(MODEL_CACHE_PATH):
        for f in ("model.safetensors", "pytorch_model.bin"):
            if os.path.exists(os.path.join(MODEL_CACHE_PATH, rev, f)):
                return True
    return False


def get_llm_service() -> QwenService:
    """Возвращает единственный экземпляр QwenService, создавая его лениво."""
    global _llm_service
    if _llm_service is None:
        if not is_model_ready():
            raise RuntimeError(MODEL_NOT_READY_MSG)
        with _llm_lock:
            if _llm_service is None:
                logger.info("Initializing QwenService (first use)...")
                _llm_service = QwenService()
                logger.info("QwenService ready")
    return _llm_service


def process_task(task_id: int, features: dict, llm_config_id: int) -> dict:
    with Session(engine) as session:
        task = session.get(MLTask, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")

        llm_config = session.get(LLMConfig, llm_config_id)
        if not llm_config:
            raise ValueError(f"LLM config {llm_config_id} not found")

        user = task.user
        if not user:
            raise ValueError("User not found for task")

        cost = llm_config.cost_per_request
        if not user.balance.has_enough(cost):
            raise ValueError(f"Insufficient balance: need {cost}, have {user.balance.credits}")

        # Извлекаем промпт из features
        prompt = features.get('prompt')
        if not prompt:
            raise ValueError("Missing 'prompt' in features")

        # Ленивая загрузка модели. Если веса ещё не скачаны, загрузка может
        # занять много времени (докачка через сеть) или упасть — в таком случае
        # задача помечается FAILED с понятным сообщением, а не висит вечно.
        try:
            llm_service = get_llm_service()
        except Exception as e:
            logger.warning(f"LLM model is not ready yet: {e}")
            raise RuntimeError(f"{MODEL_NOT_READY_MSG} Детали: {e}")

        # Генерация ответа через QwenService
        result = llm_service.generate({'prompt': prompt}, llm_config)

        # Списываем кредиты (курс берётся из Balance.CREDIT_PRICE_RUB)
        user.balance.withdraw(cost)
        rub_amount = Balance.credits_to_rub(Decimal(cost))
        transaction = Transaction(
            user_id=user.id,
            amount=rub_amount,
            transaction_type=TransactionType.WITHDRAW,
            description=f"Payment for ML task #{task.id}",
            status="approved"
        )
        session.add(transaction)

        task.status = TaskStatus.COMPLETED.value
        task.output_data = result
        task.completed_at = datetime.utcnow()
        session.add(task)
        session.add(user.balance)
        session.commit()

        return result


def callback(ch, method, properties, body):
    logger.info(f"Worker {WORKER_ID} received: {body}")
    try:
        data = json.loads(body)
        task_id = int(data.get('task_id'))
        features = data.get('features')
        llm_config_id = data.get('llm_config_id')
        if not llm_config_id:
            raise ValueError("Missing llm_config_id in message")

        result = process_task(task_id, features, llm_config_id)
        logger.info(f"Task {task_id} completed by {WORKER_ID}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        try:
            data = json.loads(body)
            task_id = int(data.get('task_id'))
            with Session(engine) as session:
                task = session.get(MLTask, task_id)
                if task:
                    task.status = TaskStatus.FAILED.value
                    task.error_message = str(e)
                    session.add(task)
                    session.commit()
        except Exception as e2:
            logger.error(f"Could not update task status: {e2}")
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection_params = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        virtual_host='/',
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS),
        heartbeat=30,
        blocked_connection_timeout=2
    )
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    logger.info(f"Worker {WORKER_ID} started, waiting for messages...")
    channel.start_consuming()


if __name__ == '__main__':
    main()