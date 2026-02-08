from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class RelationalStorageManager(ABC):
    """
    Abstract class to define the basic functionalities of a relational database system.
    """

    @abstractmethod
    def connect(self, **kwargs):
        """
        Connect to the relational database system.
        
        :param kwargs: Connection parameters (host, port, user, password, database, etc.)
        """
        pass

    @abstractmethod
    def get_connection(self):
        """
        Get the current database connection.
        
        :return: Database connection object
        """
        pass

    @abstractmethod
    def get_cursor(self, **kwargs):
        """
        Get a database cursor for executing queries.
        
        :param kwargs: Optional cursor parameters (e.g., cursor_factory)
        :return: Database cursor object
        """
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: bool = False) -> Optional[Any]:
        """
        Execute a SQL query.
        
        :param query: SQL query string
        :param params: Query parameters
        :param fetch: Whether to fetch results
        :return: Query results if fetch=True, None otherwise
        """
        pass

    @abstractmethod
    def execute_many(self, query: str, params_list: List[tuple]):
        """
        Execute a SQL query with multiple parameter sets.
        
        :param query: SQL query string
        :param params_list: List of parameter tuples
        """
        pass

    @abstractmethod
    def commit(self):
        """
        Commit the current transaction.
        """
        pass

    @abstractmethod
    def rollback(self):
        """
        Rollback the current transaction.
        """
        pass

    @abstractmethod
    def close_connection(self):
        """
        Close the connection to the relational database system.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if the database connection is active.
        
        :return: True if connected, False otherwise
        """
        pass
