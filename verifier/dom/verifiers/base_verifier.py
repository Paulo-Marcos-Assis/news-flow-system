from abc import ABC, abstractmethod
import requests
import json

class BaseVerifier(ABC):
    verification_name = "base"
    """Base class for all verifiers."""
    def __init__(self,logger):
        self.logger = logger
        
    @abstractmethod
    def verify(self, record):
        raise NotImplementedError("Subclasses must implement this method.")