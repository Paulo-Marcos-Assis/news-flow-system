from typing import Any
from abc import ABC, abstractmethod

from psycopg2.extras import RealDictCursor

class BaseAlert(ABC):

    alert_type = "base"

    @abstractmethod
    def execute_alert(self, query_execute: dict[str, Any], objetos_analise: dict[str, Any], metodo_analise: dict[str, Any], cursor: RealDictCursor) -> dict[str, Any]:
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def validate_alert(self, query_validate: dict[str, Any], objetos_analise: dict[str, Any], cursor: RealDictCursor) -> bool:
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def generate_alert(self, data: dict[str, Any], cursor: RealDictCursor):
        raise NotImplementedError("Subclasses must implement this method.")