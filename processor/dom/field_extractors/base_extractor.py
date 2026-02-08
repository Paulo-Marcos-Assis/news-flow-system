from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    field = "base"

    def __init__(self,logger):
        self.logger = logger

    @abstractmethod
    def extract_from_heuristic(self, record):
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def extract_from_model(self, record):
        raise NotImplementedError("Subclasses must implement this method.")