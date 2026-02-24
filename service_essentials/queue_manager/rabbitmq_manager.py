import pika
import os
import time
import json
from service_essentials.queue_manager.queue_manager import QueueManager
from service_essentials.utils.logger import Logger 

class RabbitMQManager(QueueManager):
    """
    RabbitMQ implementation of the QueueManager.
    """

    def __init__(self):
        self.connection = None
        self.channel = None
        self.logger = Logger(None,log_to_console=True)
        self._consuming = False
        self._declared_queues = set()  # Track declared queues for reconnection

    def connect(self):
        """
        Connect to RabbitMQ server.
        """
        try:
            # Close existing connection if any
            if self.connection and not self.connection.is_closed:
                try:
                    self.connection.close()
                except:
                    pass
            
            host = os.getenv("QUEUE_SERVER_ADDRESS", "localhost")
            port = os.getenv("QUEUE_SERVER_PORT", "5672")
            user = os.getenv("RABBIT_MQ_USER", "admin")
            pwd = os.getenv("RABBIT_MQ_PWD", "admin")
            credentials = pika.PlainCredentials(user,pwd)
            self.logger.info(f"Connecting to RabbitMQ server - {host}:{port}")
            heartbeat = int(os.getenv("RABBIT_MQ_HEARTBEAT", 3600))
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=host,
                port=int(port),
                credentials=credentials,
                heartbeat=heartbeat,
                blocked_connection_timeout=3600
            ))
            self.channel = self.connection.channel()
            self.channel.basic_qos(prefetch_count=os.getenv("PREFETCH_COUNT",1))
            self.logger.info("Connected to RabbitMQ")
        except Exception as e:
            self.logger.error(f"Failed to connect to RabbitMQ: {e}")

    def declare_queue(self, queue_name):
        """
        Declare a durable queue in RabbitMQ.
        """
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            self._declared_queues.add(queue_name)  # Track declared queues
            self.logger.info(f"Queue '{queue_name}' declared as durable.")
        except Exception as e:
            self.logger.info(f"Failed to declare queue '{queue_name}': {e}")

    def _is_connection_open(self):
        """
        Check if the connection and channel are open.
        """
        return (self.connection and self.connection.is_open and 
                self.channel and self.channel.is_open)
    
    def _ensure_connection(self):
        """
        Ensure the connection and channel are open, reconnect if necessary.
        """
        if not self._is_connection_open():
            self.logger.warning("Connection or channel is closed. Reconnecting...")
            try:
                # Close existing connections if they exist
                if self.channel and not self.channel.is_closed:
                    try:
                        self.channel.close()
                    except:
                        pass
                if self.connection and not self.connection.is_closed:
                    try:
                        self.connection.close()
                    except:
                        pass
            except:
                pass
            
            # Reconnect
            self.connect()
            
            # Redeclare all previously declared queues
            if self._declared_queues:
                self.logger.info(f"Redeclaring {len(self._declared_queues)} queues after reconnection")
                for queue_name in list(self._declared_queues):
                    try:
                        self.channel.queue_declare(queue=queue_name, durable=True)
                        self.logger.info(f"Queue '{queue_name}' redeclared as durable.")
                    except Exception as e:
                        self.logger.error(f"Failed to redeclare queue '{queue_name}': {e}")
            
            return True
        return False
    
    def _process_data_events(self):
        """
        Process pending data events to keep the connection alive.
        This should be called periodically during long operations.
        """
        try:
            if self.connection and self.connection.is_open:
                self.connection.process_data_events(time_limit=0)
        except Exception as e:
            self.logger.debug(f"Error processing data events: {e}")
    
    def publish_message(self, queue_name, message):
        """
        Publish a message to the specified queue with automatic reconnection.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Ensure connection is open
                self._ensure_connection()
                
                # Process heartbeats
                self._process_data_events()
                
                # Publish the message with persistent delivery mode
                self.channel.basic_publish(
                    exchange='',
                    routing_key=queue_name,
                    body=message,
                    properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
                )
                self.logger.info(f"Message published to queue '{queue_name}': {message}")
                return
                
            except Exception as e:
                retry_count += 1
                self.logger.error(f"Failed to publish message to queue '{queue_name}' (attempt {retry_count}/{max_retries}): {e}")
                
                if retry_count < max_retries:
                    self.logger.info("Attempting to reconnect...")
                    try:
                        self.connect()
                    except Exception as reconnect_error:
                        self.logger.error(f"Reconnection failed: {reconnect_error}")
                else:
                    self.logger.error(f"Failed to publish message after {max_retries} attempts")
                    raise

    def consume_messages(self, queue_name, callback, max_reconnect_attempts=0):
        """
        Consume messages from the specified queue and call the callback function.
        Automatically reconnects if connection is lost.

        The callback function should accept two arguments:
        - message (the content of the message)
        - acknowledge (a function to acknowledge the message)
        
        Args:
            queue_name: Name of the queue to consume from
            callback: Function to call for each message
            max_reconnect_attempts: Maximum reconnection attempts (0 = infinite)
        """
        def pika_callback(ch, method, properties, body):
            def acknowledge():
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        # Ensure connection is open before acknowledging
                        self._ensure_connection()
                        
                        # If we had to reconnect, we can't ack the old delivery tag
                        # The message will be redelivered, which is safer than losing it
                        if ch.is_open:
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            return
                        else:
                            self.logger.warning("Channel closed during acknowledge, message will be redelivered")
                            return
                            
                    except Exception as e:
                        retry_count += 1
                        self.logger.error(f"Failed to acknowledge message (attempt {retry_count}/{max_retries}): {e}")
                        
                        if retry_count < max_retries:
                            try:
                                self.connect()
                            except Exception as reconnect_error:
                                self.logger.error(f"Reconnection failed during acknowledge: {reconnect_error}")
                        else:
                            self.logger.error(f"Failed to acknowledge message after {max_retries} attempts")
                            # Don't raise - let the message be redelivered
                            return

            callback(body.decode(), acknowledge)

        reconnect_attempts = 0
        reconnect_delay = 5  # Initial delay in seconds
        max_delay = 60  # Maximum delay between reconnection attempts
        
        while True:
            try:
                # Ensure we have a valid connection
                self._ensure_connection()
                
                consumer_tag = os.uname().nodename
                
                self._consuming = True
                self.channel.basic_consume(
                    queue=queue_name, 
                    on_message_callback=pika_callback, 
                    auto_ack=False,
                    consumer_tag=consumer_tag
                )
                self.logger.info(f"Started consuming messages from queue '{queue_name}' with consumer_tag '{consumer_tag}'.")
                
                # Reset reconnect counter on successful start
                reconnect_attempts = 0
                reconnect_delay = 5
                
                self.channel.start_consuming()
                
            except Exception as e:
                self._consuming = False
                reconnect_attempts += 1
                
                self.logger.error(f"Failed to consume messages from queue '{queue_name}': {e}")
                
                # Check if we should stop trying
                if max_reconnect_attempts > 0 and reconnect_attempts >= max_reconnect_attempts:
                    self.logger.error(f"Max reconnection attempts ({max_reconnect_attempts}) reached. Stopping consumer.")
                    break
                
                self.logger.info(f"Attempting to reconnect in {reconnect_delay} seconds... (attempt {reconnect_attempts})")
                
                import time
                time.sleep(reconnect_delay)
                
                # Exponential backoff with max delay
                reconnect_delay = min(reconnect_delay * 2, max_delay)
                
                try:
                    self.connect()
                    self.logger.info("Reconnection successful, restarting consumer...")
                except Exception as reconnect_error:
                    self.logger.error(f"Reconnection failed: {reconnect_error}")
            
    def get_queue_size(self, queue_name):
        """
        Get the size of the specified queue.
        """
        # Ensure connection is open
        self._ensure_connection()
        
        try:
            queue = self.channel.queue_declare(queue=queue_name, durable=True, passive=True)
            return queue.method.message_count
        except Exception as e:
            self.logger.error(f"Failed to get queue size for '{queue_name}': {e}")
            return 0

    def declare_exchange(self, exchange_name, exchange_type='topic'):
        """
        Declare an exchange in RabbitMQ.
        """
        try:
            self.channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=True)
            self.logger.info(f"Exchange '{exchange_name}' of type '{exchange_type}' declared.")
        except Exception as e:
            self.logger.error(f"Failed to declare exchange '{exchange_name}': {e}")

    def bind_queue_to_exchange(self, queue_name, exchange_name, routing_key):
        """
        Bind a queue to an exchange with a routing key.
        """
        try:
            self.channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)
            self.logger.info(f"Queue '{queue_name}' bound to exchange '{exchange_name}' with routing key '{routing_key}'.")
        except Exception as e:
            self.logger.error(f"Failed to bind queue '{queue_name}' to exchange '{exchange_name}': {e}")

    def publish_to_exchange(self, exchange_name, routing_key, message):
        """
        Publish a message to an exchange with a routing key.
        """
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                self._ensure_connection()
                
                # Serializa a mensagem para JSON se for um dict
                if isinstance(message, dict):
                    message_body = json.dumps(message)
                else:
                    message_body = message
                
                self.channel.basic_publish(
                    exchange=exchange_name,
                    routing_key=routing_key,
                    body=message_body,
                    properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
                )
                self.logger.info(f"Message published to exchange '{exchange_name}' with routing key '{routing_key}': {message}")
                return
            except Exception as e:
                retry_count += 1
                last_error = e
                self.logger.error(f"Failed to publish message to exchange '{exchange_name}' (attempt {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    self.logger.info(f"Waiting 2 seconds before retry...")
                    try:
                        time.sleep(2)
                    except:
                        pass
                    self.logger.info(f"Attempting to reconnect...")
                    try:
                        # Force close old connection
                        self.connection = None
                        self.channel = None
                        self.connect()
                        self.logger.info(f"Reconnection successful, retrying publish...")
                    except Exception as reconnect_error:
                        self.logger.error(f"Reconnection failed: {reconnect_error}")
        
        # If we exhausted all retries, raise the last error
        if last_error:
            raise last_error

    def get_persistent_properties(self):
        """
        Get persistent message properties for RabbitMQ.
        Returns BasicProperties with delivery_mode=2 for persistent messages.
        """
        return pika.BasicProperties(delivery_mode=2)

    def close_connection(self):
        """
        Close the connection to RabbitMQ.
        """
        try:
            if self.channel:
                self.channel.close()
            if self.connection:
                self.connection.close()
            self.logger.info("RabbitMQ connection closed.")
        except Exception as e:
            self.logger.error(f"Failed to close RabbitMQ connection: {e}")