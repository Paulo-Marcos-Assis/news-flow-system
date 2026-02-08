from abc import ABC, abstractmethod

class BaseGrouper(ABC):
    
    def __init__(self,logger):
        self.logger = logger

    @abstractmethod
    def group(self, item):
        raise NotImplementedError("Subclasses must implement this method.")