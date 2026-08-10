import pika

# Параметры подключения
connection_params = pika.ConnectionParameters(
    host='rabbitmq',  # Замените на адрес вашего RabbitMQ сервера
    port=5672,          # Порт по умолчанию для RabbitMQ
    virtual_host='/',   # Виртуальный хост (обычно '/')
    credentials=pika.PlainCredentials(
        username='rmuser',  # Имя пользователя по умолчанию
        password='rmpassword'   # Пароль по умолчанию
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

def send_task(message:str):
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    
    # Имя очереди
    queue_name = 'ml_task_queue'

    # Отправка сообщения
    channel.queue_declare(queue=queue_name)  # Создание очереди (если не существует)

    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message
    )

    # Закрытие соединения
    connection.close()