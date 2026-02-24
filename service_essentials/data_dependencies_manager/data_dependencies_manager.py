from abc import ABC, abstractmethod
from typing import Dict, Optional, List, Any


class DataDependenciesManager(ABC):
    """
    Abstract class for managing data dependencies between entities.
    Provides interface for loading and querying FK relationships.
    """

    @abstractmethod
    def load_dependencies(self, source: str) -> bool:
        """
        Load dependency configuration for a specific data source.

        :param source: Data source identifier (e.g., 'esfinge', 'pncp')
        :return: True if dependencies loaded successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_entity_dependencies(self, source: str, entity_type: str) -> Dict[str, Dict[str, str]]:
        """
        Get all FK dependencies for a specific entity.

        :param source: Data source identifier
        :param entity_type: Entity type name
        :return: Dictionary of dependencies in format:
                 {
                     "referenced_entity": {
                         "fk": "FK_field_name",
                         "pk": "PK_field_name"
                     }
                 }
        """
        pass

    @abstractmethod
    def get_dependent_entities(self, source: str, entity_type: str) -> Dict[str, Dict[str, str]]:
        """
        Get all entities that depend on this entity (inverse dependencies).

        :param source: Data source identifier
        :param entity_type: Entity type name
        :return: Dictionary of dependent entities in same format as get_entity_dependencies
        """
        pass

    @abstractmethod
    def has_dependencies(self, source: str, entity_type: str) -> bool:
        """
        Check if an entity has any FK dependencies.

        :param source: Data source identifier
        :param entity_type: Entity type name
        :return: True if entity has dependencies, False otherwise
        """
        pass

    @abstractmethod
    def get_all_entities(self, source: str) -> List[str]:
        """
        Get list of all entities defined for a source.

        :param source: Data source identifier
        :return: List of entity names
        """
        pass

    @abstractmethod
    def get_static_reference_entities(self, source: str) -> Dict[str, Dict[str, Any]]:
        """
        Get entities that are static reference data (no temporal dependencies).

        :param source: Data source identifier
        :return: Dictionary of static entities with their configuration
                 e.g., {"tipo_pessoa": {"csv_file": "tipo_pessoa.csv"}}
        """
        pass

    @abstractmethod
    def get_temporal_reference_entities(self, source: str) -> Dict[str, Dict[str, Any]]:
        """
        Get entities that are temporal reference data.

        :param source: Data source identifier
        :return: Dictionary of temporal entities with their configuration
                 e.g., {"comissao_licitacao": {"csv_file": "comissao_2021.csv", "year": "2021"}}
        """
        pass

    @abstractmethod
    def is_loaded(self, source: str) -> bool:
        """
        Check if dependencies are loaded for a source.

        :param source: Data source identifier
        :return: True if loaded, False otherwise
        """
        pass

    @abstractmethod
    def reload_dependencies(self, source: str) -> bool:
        """
        Reload dependencies for a source (useful for updates).

        :param source: Data source identifier
        :return: True if reload successful, False otherwise
        """
        pass

    @abstractmethod
    def get_all_entity_types(self, source: str) -> List[str]:
        """
        Get all entity types for a data source (same as get_all_entities).

        :param source: Data source identifier
        :return: List of entity type names
        """
        pass

    @abstractmethod
    def get_loaded_sources(self) -> List[str]:
        """
        Get list of all loaded data sources.

        :return: List of data source identifiers
        """
        pass

