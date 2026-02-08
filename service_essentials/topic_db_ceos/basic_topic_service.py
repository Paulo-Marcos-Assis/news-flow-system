import pika
from pika.exceptions import AMQPConnectionError

import time
import os

import sys
from abc import ABC, abstractmethod

class BasicTopicService(ABC):

    def __init__(self, queue_name: str = '', host: str = "localhost"):
        self.host = host
        self.queue_name = queue_name

        self.connection = None
        self.channel = None

    def connect(self):
        while True:
            try:

                credentials = pika.PlainCredentials(
                    username=os.getenv("RABBITMQ_DEFAULT_USER", "admin"),
                    password=os.getenv("RABBITMQ_DEFAULT_PASS", "admin")
                )

                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=self.host,
                        credentials=credentials
                    )
                )

                self.channel = self.connection.channel()

                self.channel.exchange_declare(exchange='topic_db_insert_update', exchange_type='topic')

                result = self.channel.queue_declare(self.queue_name, exclusive=True)
                result_queue = result.method.queue

                binding_keys = sys.argv[1:]
                if not binding_keys:
                    sys.stderr.write("Usage: %s [binding_key]...\n" % sys.argv[0])
                    sys.exit(1)

                for binding_key in binding_keys:
                    self.channel.queue_bind(exchange='topic_db_insert_update', queue=result_queue, routing_key=binding_key)

                print(f"Connected to RabbitMQ and listening route {binding_keys}.")

                break
            except AMQPConnectionError as e:
                print("Cannot connect to RabbitMQ. Retrying in 5 seconds...")
                print(e)
                time.sleep(5)

    def start_consuming(self):
        while True:
            if self.connection is None or self.connection.is_closed:
                self.connect()

            try:
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self.callback,
                    auto_ack=True
                )

                print(f"[*] Waiting for messages on '{self.queue_name}'... To exit press CTRL+C")

                self.channel.start_consuming()

            except AMQPConnectionError:
                print("Connection lost. Reconnecting in 5 seconds...")
                time.sleep(5)

    @abstractmethod
    def callback(self, ch, method, properties, body):
        pass