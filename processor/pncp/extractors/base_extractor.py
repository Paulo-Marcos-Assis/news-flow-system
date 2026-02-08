from abc import ABC, abstractmethod

DEFAULT_VALUE = None

class BaseExtractor(ABC):
    field_name = "base"
    
    def __init__(self, logger, object_storage_manager=None):
        self.logger = logger
        self.object_storage_manager = object_storage_manager

    @abstractmethod
    def extract(self, record):
        raise NotImplementedError("Subclasses must implement this method.")