from abc import ABC, abstractmethod


class BaseExtractor(ABC):
    field_name = "base"

    def __init__(self, logger):
        self.logger = logger

    @abstractmethod
    def extract(self, record):
        raise NotImplementedError("Subclasses must implement this method.")
