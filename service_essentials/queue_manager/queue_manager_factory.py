class QueueManagerFactory:
    """
    Factory class to instantiate the appropriate QueueManager based on environment variable.
    """
    @staticmethod
    def get_queue_manager():
        import os
        queue_manager_type = os.getenv("QUEUE_MANAGER", "RabbitMQ").lower()
        if queue_manager_type == "rabbitmq":
            from service_essentials.queue_manager.rabbitmq_manager import RabbitMQManager
            return RabbitMQManager()
        else:
            raise ValueError(f"Unsupported Queue Manager: {queue_manager_type}")