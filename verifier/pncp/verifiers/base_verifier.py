from abc import ABC, abstractmethod

class BaseVerifier(ABC):
    """
    Abstract base class for all verifiers.
    """
    destination_field = "base"
    
    def __init__(self, logger):
        self.logger = logger

    @abstractmethod
    def verify(self, data):
        """
        Verifies the data for the destination field.

        Args:
            data: The entire dictionary of extracted data.

        Returns:
            A tuple (bool, str).
            The first element is True if verification passes, False otherwise.
            The second element is a failure message, or None if successful.
        """
        raise NotImplementedError("Subclasses must implement this method.")
