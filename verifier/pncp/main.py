import importlib
import os

from service_essentials.utils.logger import Logger
from service_essentials.exceptions.fail_queue_exception import FailQueueException
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from verifiers.base_verifier import BaseVerifier


class VerifierPNCP(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.verifiers = self.load_verifiers()

    def process_message(self, record):
        """
        Processes a single record from the queue, applying all registered verifiers.
        """
        failures = {}
        
        data_to_verify = record
        if not isinstance(data_to_verify, dict):
            raise FailQueueException({"error": "Record does not contain an dictionary."})

        for dest_field, verifier in self.verifiers.items():
            verified, msg = verifier.verify(data_to_verify)
            if not verified:
                self.logger.warning(f"Verification failed for destination field '{dest_field}': {msg}")
                failures[dest_field] = msg

        if failures:
            raise FailQueueException(failures)

        self.logger.info("Record verified successfully!")
        return record

    def load_verifiers(self):
        """
        Dynamically loads verifier classes from the 'verifiers' directory.
        """
        path = "verifiers"
        verifiers = {}
        if not os.path.isdir(path):
            self.logger.error(f"Verifiers directory not found at '{path}'")
            return verifiers
            
        for file in os.listdir(path):
            if file.endswith("_verifier.py") and file != "base_verifier.py":
                module_name = f"verifiers.{file[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for attr in dir(module):
                        cls = getattr(module, attr)
                        if isinstance(cls, type) and issubclass(cls, BaseVerifier) and cls is not BaseVerifier:
                            instance = cls(self.logger)
                            verifiers[instance.destination_field] = instance
                            self.logger.info(f"Loaded verifier for destination field: {instance.destination_field}")
                except ImportError as e:
                    self.logger.error(f"Failed to import module {module_name}: {e}")
        return verifiers


if __name__ == '__main__':
    logger = Logger(log_to_console=True)
    processor = VerifierPNCP()
    processor.start()
