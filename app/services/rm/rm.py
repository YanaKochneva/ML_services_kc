import pika
import os
import json

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'rmuser')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASSWORD', 'rmpassword')

connection_params = pika.ConnectionParameters(
    host=RABBITMQ_HOST,  
    port=5672,         
    virtual_host='/',  
    credentials=pika.PlainCredentials(
        username=RABBITMQ_USER, 
        password=RABBITMQ_PASS   
    ),
    heartbeat=30,
    blocked_connection_timeout=2
)

def send_task(message: dict):
    connection = pika.BlockingConnection(connection_params)
    channel = connection.channel()
    
    queue_name = 'ml_task_queue'

    channel.queue_declare(queue=queue_name, durable=True) 

    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message)
    )

    connection.close()