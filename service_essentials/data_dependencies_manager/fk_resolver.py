from typing import Dict, Any, Optional
from datetime import datetime


class FKResolver:
    """
    Helper class for resolving foreign key dependencies.
    Separates FK resolution logic from the base service class.
    """

    def __init__(self, dependencies_manager, document_storage_manager, pendency_manager, logger):
        """
        Initialize FK resolver.
        
        :param dependencies_manager: DataDependenciesManager instance
        :param document_storage_manager: DocumentStorageManager instance
        :param pendency_manager: PendencyManager instance
        :param logger: Logger instance
        """
        self.dependencies_manager = dependencies_manager
        self.document_storage_manager = document_storage_manager
        self.pendency_manager = pendency_manager
        self.logger = logger

    def resolve_fk_dependencies(self, message: Dict[str, Any]) -> bool:
        """
        Resolve all FK dependencies for a message.
        
        :param message: Message to process
        :return: Enriched message with FK raw_data_ids
        """
        data_source = message.get("data_source", "").lower()
        entity_type = message.get("entity_type")

        if not data_source or not entity_type:
            self.logger.info("No data_source or entity_type in message, skipping FK resolution")
            return message

        # Load dependencies for this source
        if not self.dependencies_manager.is_loaded(data_source):
            loaded = self.dependencies_manager.load_dependencies(data_source)
            if not loaded:
                self.logger.info(f"No dependencies available for '{data_source}', skipping FK resolution")
                return message

        # Get dependencies for this entity
        entity_deps = self.dependencies_manager.get_entity_dependencies(data_source, entity_type)

        if not entity_deps:
            self.logger.debug(f"No dependencies defined for entity '{entity_type}'")
            return message

        self.logger.info(f"Processing {len(entity_deps)} FK dependencies for '{entity_type}'")

        # Process each FK dependency
        all_dependencies_resolved = True
        for ref_entity, fk_config in entity_deps.items():
            if not self._resolve_single_fk(message, data_source, entity_type, ref_entity, fk_config):
                all_dependencies_resolved = False

        return all_dependencies_resolved

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """
        Safely retrieves a value from a nested dictionary using a dot-notation path.
        Example: _get_nested_value(data, "key1.key2")
        """
        if not path:
            return None
        keys = path.split('.')
        current_level = data
        for key in keys:
            if not isinstance(current_level, dict):
                return None
            current_level = current_level.get(key)
            if current_level is None:
                return None
        return current_level

    def _resolve_single_fk(self, message: Dict[str, Any], source: str, entity_type: str,
                          ref_entity: str, fk_config: Dict[str, str]) -> bool:
        """
        Resolve a single FK dependency.
        
        :param message: Message being processed
        :param source: Data source
        :param entity_type: Current entity type
        :param ref_entity: Referenced entity name
        :param fk_config: FK configuration with 'fk' and 'pk' fields
        """
        fk_field = fk_config.get("fk")  # Field name in current message
        pk_field = fk_config.get("pk")  # Primary key field in referenced entity
        mandatory = fk_config.get("mandatory", False)

        # Get the FK value from the message, now with support for nested keys
        fk_value = self._get_nested_value(message, fk_field)

        if not fk_value and mandatory is True:
            self.logger.error(f"Mandatory reference field {fk_field} is empty. Message {message} will not be processed.")
            return False

        #if fk_value is None or fk_value == "", it means that the foreign key is not mandatory
        if fk_value is None or fk_value == "":
            self.logger.debug(f"FK field '{fk_field}' not found in message, skipping")
            return True

        # Query document storage for the referenced entity
        collection_name = f"{source}.{ref_entity}"
        query = {pk_field: fk_value}

        self.logger.info(f"Looking up FK: {ref_entity}.{pk_field} = {fk_value}")

        try:
            referenced_doc = self.document_storage_manager.find_document(collection_name, query)

            if referenced_doc:
                # FK data found - check if referenced document has all its pendencies resolved
                referenced_raw_data_id = referenced_doc.get("_id")
                
                # Check if the referenced document itself has unresolved pendencies
                if self.pendency_manager.check_all_pendencies_resolved(source, ref_entity, referenced_raw_data_id):
                    # Referenced document is fully resolved - can use it
                    message[ref_entity] = referenced_doc
                    #self.logger.info(f"FK resolved: raw_data_id = {referenced_raw_data_id}")
                    return True
                else:
                    # Referenced document exists but has unresolved pendencies
                    #self.logger.warning(f"FK found but referenced document {referenced_raw_data_id} has unresolved pendencies, creating pendency")
                    pass
            else:
                # FK data not found
                #self.logger.warning(f"FK not found for {ref_entity}.{pk_field} = {fk_value}, creating pendency")
                pass
            
            # Create pendency (common path for both not found and incomplete)
            self.pendency_manager.store_pendency(
                source=source,
                entity_type=entity_type,
                ref_entity=ref_entity,
                fk_field=fk_field,
                pk_field=pk_field,
                fk_value=fk_value,
                message=message
            )
            return False

        except Exception as e:
            self.logger.error(f"Error querying FK data for {ref_entity}: {e}")
            return False
