import pika
import os
import json

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'rmuser')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASSWORD', 'rmpassword')

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,  # Замените на адрес вашего RabbitMQ сервера
    port=5672,          # Порт по умолчанию для RabbitMQ
    virtual_host='/',   # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username=RABBITMQ_USER,  # Имя пользователя по умолчанию
        password=RABBITMQ_PASS   # Пароль по умолчанию
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

def send_task(message: dict):
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    
    # Имя очереди
    queue_name = 'ml_task_queue'

    # Отправка сообщения
    channel.queue_declare(queue=queue_name, durable=True)  # Создание очереди (если не существует)

    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message)
    )

    # Закрытие соединения
    connection.close()