import pika
import json
import logging
import os
import sys
from datetime import datetime
from decimal import Decimal
from sqlmodel import Session
from database.database import engine
from models.ml_task import MLTask
from models.enums import TaskStatus, TransactionType
from models.transaction import Transaction
from models.llm_config import LLMConfig
from services.qwen_service import QwenService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Настройки RabbitMQ ===
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'rmuser')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASSWORD', 'rmpassword')
QUEUE_NAME = 'ml_task_queue'
WORKER_ID = os.getenv('WORKER_ID', 'worker-1')

llm_service = QwenService()

def process_task(task_id: int, features: dict, llm_config_id: int) -> dict:
    """
    Основная логика обработки одной задачи.
    Возвращает результат генерации.
    """
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

        # Валидация входных данных (опционально, но рекомендуется)
        validation_errors = llm_service.validate_data(features, llm_config)
        if validation_errors:
            task.add_validation_error(validation_errors[0])
            session.add(task)
            session.commit()
            raise ValueError(f"Validation errors: {validation_errors}")

        # Генерация ответа (используем ваш сервис)
        result = llm_service.generate(features, llm_config)

        # Списываем кредиты
        user.balance.withdraw(cost)
        # Создаём транзакцию списания
        # Цена в рублях – берём из модели Balance (если есть метод credits_to_rub)
        rub_amount = Decimal(cost) * Decimal('30.0')  # можно заменить на Balance.credits_to_rub
        transaction = Transaction(
            user_id=user.id,
            amount=rub_amount,
            transaction_type=TransactionType.WITHDRAW,
            description=f"Payment for ML task #{task.id}",
            status="approved"
        )
        session.add(transaction)

        # Обновляем задачу
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
        # Пытаемся пометить задачу как FAILED
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
            # Всегда подтверждаем, чтобы не засорять очередь
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
    channel.basic_qos(prefetch_count=1)   # round‑robin
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=False)
    logger.info(f"Worker {WORKER_ID} started, waiting for messages...")
    channel.start_consuming()

if __name__ == '__main__':
    main()