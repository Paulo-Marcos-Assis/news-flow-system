from abc import ABC, abstractmethod

class BaseVerifier(ABC):
    field_name = "base"
    
    def __init__(self,logger):
        self.logger = logger

    @abstractmethod
    def verify(self, record):
        raise NotImplementedError("Subclasses must implement this method.")
