from abc import ABC, abstractmethod

class QueueManager(ABC):
    """
    Abstract class to define the basic functionalities of a message-queue system.
    """

    @abstractmethod
    def connect(self, **kwargs):
        """
        Connect to the message queue system.
        """
        pass

    @abstractmethod
    def declare_queue(self, queue_name):
        """
        Declare a queue.
        """
        pass

    @abstractmethod
    def publish_message(self, queue_name, message):
        """
        Publish a message to the specified queue.
        """
        pass

    @abstractmethod
    def consume_messages(self, queue_name, callback):
        """
        Consume messages from the specified queue.
        """
        pass
    
    @abstractmethod
    def get_queue_size(self,queue_name):
        """
        Get the size of the specified queue.
        """
        pass

    @abstractmethod
    def declare_exchange(self, exchange_name, exchange_type='topic'):
        """
        Declare an exchange.
        """
        pass

    @abstractmethod
    def bind_queue_to_exchange(self, queue_name, exchange_name, routing_key):
        """
        Bind a queue to an exchange with a routing key.
        """
        pass

    @abstractmethod
    def publish_to_exchange(self, exchange_name, routing_key, message):
        """
        Publish a message to an exchange with a routing key.
        """
        pass

    @abstractmethod
    def get_persistent_properties(self):
        """
        Get persistent message properties for the queue system.
        Returns properties object that ensures message persistence.
        """
        pass

    @abstractmethod
    def close_connection(self):
        """
        Close the connection to the message queue system.
        """
        pass