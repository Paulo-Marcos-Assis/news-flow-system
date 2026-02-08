from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class DocumentStorageManager(ABC):
    """
    Abstract class for a document storage system.
    Provides interface for storing and retrieving documents from NoSQL databases.
    """

    @abstractmethod
    def connect(self, host: str, port: int, username: str, password: str, database: str, **kwargs):
        """
        Connect to the document storage server.

        :param host: The server host.
        :param port: The server port.
        :param username: Username for authentication.
        :param password: Password for authentication.
        :param database: Database name.
        :param kwargs: Additional connection parameters.
        """
        pass

    @abstractmethod
    def insert_document(self, collection: str, document: Dict[str, Any]) -> str:
        """
        Insert a document into a collection.
        
        The implementation MUST generate a unique ID if the document doesn't have one.
        This ensures database-agnostic behavior regardless of the underlying storage system.

        :param collection: The name of the collection.
        :param document: The document to insert (as a dictionary). May or may not contain '_id'.
        :return: The unique ID of the inserted document (as string).
                 - MongoDB: Returns str(ObjectId)
                 - Other DBs: Returns generated UUID or auto-increment ID
        """
        pass

    @abstractmethod
    def insert_many_documents(self, collection: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents into a collection.

        :param collection: The name of the collection.
        :param documents: List of documents to insert.
        :return: List of IDs of the inserted documents.
        """
        pass

    @abstractmethod
    def find_document(self, collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find a single document in a collection.

        :param collection: The name of the collection.
        :param query: Query filter as a dictionary.
        :return: The found document or None.
        """
        pass

    @abstractmethod
    def find_documents(self, collection: str, query: Dict[str, Any], limit: int = 0) -> List[Dict[str, Any]]:
        """
        Find multiple documents in a collection.

        :param collection: The name of the collection.
        :param query: Query filter as a dictionary.
        :param limit: Maximum number of documents to return (0 = no limit).
        :return: List of found documents.
        """
        pass

    @abstractmethod
    def update_document(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update a single document in a collection.

        :param collection: The name of the collection.
        :param query: Query filter to find the document.
        :param update: Update operations to apply.
        :return: Number of documents modified.
        """
        pass

    @abstractmethod
    def update_many_documents(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """
        Update multiple documents in a collection.

        :param collection: The name of the collection.
        :param query: Query filter to find documents.
        :param update: Update operations to apply.
        :return: Number of documents modified.
        """
        pass

    @abstractmethod
    def delete_document(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Delete a single document from a collection.

        :param collection: The name of the collection.
        :param query: Query filter to find the document.
        :return: Number of documents deleted.
        """
        pass

    @abstractmethod
    def delete_many_documents(self, collection: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents from a collection.

        :param collection: The name of the collection.
        :param query: Query filter to find documents.
        :return: Number of documents deleted.
        """
        pass

    @abstractmethod
    def count_documents(self, collection: str, query: Dict[str, Any] = None) -> int:
        """
        Count documents in a collection.

        :param collection: The name of the collection.
        :param query: Query filter (optional).
        :return: Number of documents matching the query.
        """
        pass

    @abstractmethod
    def collection_exists(self, collection: str) -> bool:
        """
        Check if a collection exists.

        :param collection: The name of the collection.
        :return: True if collection exists, False otherwise.
        """
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        List all collection names in the database.

        :return: List of collection names.
        """
        pass

    @abstractmethod
    def create_index(self, collection: str, keys: List[tuple], unique: bool = False, name: str = None) -> str:
        """
        Create an index on a collection.

        :param collection: The name of the collection.
        :param keys: List of (field_name, direction) tuples. Direction: 1 for ascending, -1 for descending.
                     Example: [("field1", 1), ("field2", -1)] creates compound index.
        :param unique: Whether the index should enforce uniqueness.
        :param name: Optional custom name for the index.
        :return: Name of the created index.
        """
        pass

    @abstractmethod
    def ensure_indexes(self, collection: str, indexes: List[Dict[str, Any]]) -> List[str]:
        """
        Ensure multiple indexes exist on a collection (creates if missing).

        :param collection: The name of the collection.
        :param indexes: List of index specifications. Each dict should contain:
                       - 'keys': List of (field_name, direction) tuples
                       - 'unique': Optional boolean (default: False)
                       - 'name': Optional custom name
        :return: List of index names created/ensured.
        """
        pass

    @abstractmethod
    def close_connection(self):
        """
        Close the connection to the document storage server.
        """
        pass

