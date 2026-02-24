from typing import Dict, Any, Optional
from datetime import datetime


class PendencyManager:
    """
    Helper class for managing FK pendencies.
    Handles storing and resolving pendencies when FKs are missing.
    """

    def __init__(self, dependencies_manager, document_storage_manager, logger):
        """
        Initialize pendency manager.
        
        :param dependencies_manager: DataDependenciesManager instance
        :param document_storage_manager: DocumentStorageManager instance
        :param logger: Logger instance
        """
        self.dependencies_manager = dependencies_manager
        self.document_storage_manager = document_storage_manager
        self.logger = logger
        self.resolution_stack = set()  # Track messages being resolved to prevent infinite loops

    def store_pendency(self, source: str, entity_type: str, ref_entity: str,
                      fk_field: str, pk_field: str, fk_value: Any, message: Dict[str, Any]) -> Optional[str]:
        """
        Store a pendency when FK data is not available.
        
        :param source: Data source (e.g., 'esfinge', 'pncp')
        :param entity_type: Entity type that has the missing FK
        :param ref_entity: Referenced entity that is missing
        :param fk_field: FK field name in the message
        :param pk_field: PK field name in the referenced entity
        :param fk_value: Value of the FK
        :param message: Original message
        :return: Pendency ID if stored successfully, None otherwise
        """
        pendency_collection = f"{source}.{entity_type}.pendency"

        # We need to test this implementation that keeps track the historical of pendencies
        # if we have performance issues, we can use a different approach of deleting resolved pendencies
        # Note: MongoDB will automatically generate a unique _id (ObjectId) when inserting
        pendency = {
            "missing_entity": ref_entity,
            "raw_data_id": message.get("raw_data_id"),
            "missing_fk_field": fk_field,
            "missing_pk_field": pk_field,
            "fk_value": fk_value,
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        }

        try:
            pendency_id = self.document_storage_manager.insert_document(pendency_collection, pendency)
            self.logger.info(f"Stored pendency with ID: {pendency_id} in {pendency_collection}")
            return pendency_id
        except Exception as e:
            self.logger.error(f"Failed to store pendency: {e}")
            return None

    def resolve_pendencies(self, source: str, entity_type: str, message: Dict[str, Any]) -> int:
        """
        Check for pendencies that were waiting for this record and merge their fields into the current message.
        
        This method looks for messages that were pending because they needed this entity as a FK.
        When found, it brings all the pending message fields into the current message.
        
        :param source: Data source
        :param entity_type: Current entity type (the entity that just arrived)
        :param message: Current message with data (will be enriched with pending fields)
        :return: Number of pendencies resolved
        """
        # Get dependent entities from dependencies manager
        dependent_entities = self.dependencies_manager.get_dependent_entities(source, entity_type)

        if not dependent_entities:
            self.logger.debug(f"No dependent entities for '{entity_type}'")
            return 0

        resolved_count = 0

        # Get the PK value from the current message
        for dep_entity, fk_config in dependent_entities.items():
            pk_field = fk_config.get("pk")
            self.logger.debug(f"DEBUG pk_field: {pk_field}")
            self.logger.debug(f"DEBUG message: {message}")
            pk_value = message.get(pk_field)
            self.logger.debug(f"DEBUG pk_value: {pk_value}")

            if pk_value is None:
                self.logger.debug(f"DEBUG pk_value is None")
                continue

            # Look for pendencies waiting for this FK
            pendency_collection = f"{source}.{dep_entity}.pendency"
            query = {
                "missing_entity": entity_type,
                "missing_pk_field": pk_field,
                "fk_value": pk_value,
                "resolved": False
            }

            try:
                pendencies = self.document_storage_manager.find_documents(pendency_collection, query)

                if pendencies:
                    self.logger.info(f"Found {len(pendencies)} pendencies to resolve for {dep_entity}")

                    for pendency in pendencies:
                        # Retrieve the original pending message from document storage
                        pending_message = self.document_storage_manager.find_document(
                            f"{source}.{dep_entity}", 
                            {"_id": pendency["raw_data_id"]}
                        )
                        
                        if not pending_message:
                            self.logger.error(f"Error solving pendency for message raw_data_id {message['raw_data_id']}: Could not find message with raw_data_id: {pendency['raw_data_id']}")
                            continue
                        
                        # Mark this specific pendency as resolved in the pendency collection
                        # The resolved_by_raw_data_id field stores which message resolved this pendency
                        # Note: A message may have multiple pendencies (one per missing FK)
                        # Each pendency has a unique _id
                        self.document_storage_manager.update_document(
                            pendency_collection,
                            {"_id": pendency["_id"]},  # Use unique pendency _id
                            {
                                "resolved": True,
                                "resolved_at": datetime.now().isoformat(),
                                "resolved_by_raw_data_id": message.get("raw_data_id")  # Track which message resolved it
                            }
                        )
                        self.logger.info(f"Marked pendency {pendency['_id']} as resolved for {dep_entity} message {pendency['raw_data_id']}")
                        
                        resolved_count += 1
                        
                        # Check if ALL pendencies for this message are now resolved
                        # Only merge if the message is fully resolved
                        if self.check_all_pendencies_resolved(source, dep_entity, pendency["raw_data_id"]):
                            self.logger.info(f"All pendencies resolved for {dep_entity} message {pendency['raw_data_id']}, merging into current message")
                            
                            # Merge pending message into current message using nested structure
                            # Create entity array if it doesn't exist
                            if dep_entity not in message:
                                message[dep_entity] = []
                            
                            # Add pending message to the entity's array
                            message[dep_entity].append(pending_message)
                            self.logger.debug(f"Added pending {dep_entity} message to array (total: {len(message[dep_entity])})")
                            
                            self.logger.info(f"Merged pending {dep_entity} into current message array")
                        else:
                            self.logger.info(f"Message {pendency['raw_data_id']} still has unresolved pendencies, not merging yet")

            except Exception as e:
                self.logger.error(f"Error resolving pendencies for {dep_entity}: {e}")

        if resolved_count > 0:
            self.logger.info(f"Resolved {resolved_count} total pendencies for '{entity_type}'")

        return resolved_count

    def check_all_pendencies_resolved(self, source: str, entity_type: str, raw_data_id: str) -> bool:
        """
        Check if all pendencies for a specific message are resolved.
        
        :param source: Data source
        :param entity_type: Entity type
        :param raw_data_id: Raw data ID of the message
        :return: True if all pendencies are resolved, False otherwise
        """
        pendency_collection = f"{source}.{entity_type}.pendency"
        
        try:
            # Find all pendencies for this message
            unresolved_pendencies = self.document_storage_manager.find_documents(
                pendency_collection,
                {"raw_data_id": raw_data_id, "resolved": False}
            )
            
            if not unresolved_pendencies:
                self.logger.info(f"All pendencies resolved for {entity_type} with raw_data_id: {raw_data_id}")
                return True
            else:
                self.logger.debug(f"{len(unresolved_pendencies)} unresolved pendencies remaining for {raw_data_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error checking pendencies for {raw_data_id}: {e}")
            return False

    def resolve_pendencies_recursive(self, source: str, entity_type: str, message: Dict[str, Any], 
                                    max_depth: int = 20) -> int:
        """
        Recursively resolve pendencies with loop prevention and cascading resolution.
        
        When a message arrives:
        1. Resolve immediate pendencies (messages waiting for this entity)
        2. Merge fully resolved messages into current message (only if ALL their pendencies are resolved)
        3. For each merged message, recursively check if it can resolve other pendencies
        4. Continue cascading until no more resolutions or max depth reached
        
        Loop Prevention:
        - Resolution stack tracks messages being processed to detect circular dependencies
        - Max depth limit prevents runaway recursion (default: 20 levels)
        
        :param source: Data source (e.g., 'esfinge', 'pncp')
        :param entity_type: Entity type that just arrived (e.g., 'processo_licitatorio')
        :param message: Message with data (will be enriched with merged pending messages)
        :param max_depth: Maximum recursion depth to prevent infinite loops (default: 20)
        :return: Total number of pendencies resolved (including cascading resolutions)
        """
        raw_data_id = message.get("raw_data_id")
        
        # Prevent infinite loops - check if we're already resolving this message
        resolution_key = f"{source}.{entity_type}.{raw_data_id}"
        if resolution_key in self.resolution_stack:
            self.logger.warning(f"Circular dependency detected for {resolution_key}, stopping recursion")
            return 0
        
        if max_depth <= 0:
            self.logger.warning(f"Maximum recursion depth reached for {resolution_key}, stopping")
            return 0
        
        # Add to resolution stack
        self.resolution_stack.add(resolution_key)
        
        try:
            total_resolved = 0
            
            # Step 1: Resolve immediate pendencies (messages waiting for this entity)
            immediate_resolved = self.resolve_pendencies(source, entity_type, message)
            total_resolved += immediate_resolved
            
            if immediate_resolved > 0:
                # Step 2: Check if any of the resolved messages now have all their pendencies resolved
                dependent_entities = self.dependencies_manager.get_dependent_entities(source, entity_type)
                
                if dependent_entities:
                    for dep_entity in dependent_entities.keys():
                        # Get the pending messages we just merged
                        # Note: If a message is in this array, it means ALL its pendencies were resolved
                        # (resolve_pendencies only merges fully resolved messages)
                        if dep_entity in message:
                            for pending_msg in message[dep_entity]:
                                pending_raw_id = pending_msg.get("raw_data_id")
                                self.logger.info(f"Message {pending_raw_id} fully resolved, checking cascading pendencies")
                                
                                # Recursively resolve pendencies that depend on this now-resolved message
                                cascading_resolved = self.resolve_pendencies_recursive(
                                    source, 
                                    dep_entity, 
                                    pending_msg,
                                    max_depth - 1
                                )
                                total_resolved += cascading_resolved
            
            return total_resolved
            
        finally:
            # Remove from resolution stack
            self.resolution_stack.discard(resolution_key)