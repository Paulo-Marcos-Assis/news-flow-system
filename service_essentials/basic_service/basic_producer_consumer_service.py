from abc import ABC, abstractmethod
import os
import json
import traceback
from service_essentials.utils.logger import Logger
from service_essentials.queue_manager.queue_manager_factory import QueueManagerFactory
from service_essentials.object_storage_manager.object_storage_manager_factory import ObjectStoreManagerFactory
from service_essentials.document_storage_manager.document_storage_manager_factory import DocumentStorageManagerFactory
from service_essentials.data_dependencies_manager.data_dependencies_manager_factory import DataDependenciesManagerFactory
from service_essentials.data_dependencies_manager.fk_resolver import FKResolver
from service_essentials.data_dependencies_manager.pendency_manager import PendencyManager
from service_essentials.data_dependencies_manager.index_manager import IndexManager
from service_essentials.exceptions.fail_queue_exception import FailQueueException
import sentry_sdk


class BasicProducerConsumerService(ABC):
    def __init__(self):
        """
        Initialize the service with input, output, and fail queues using a single QueueManager.
        """
        self.service_name = os.getenv("SERVICE_NAME", "default_service")
        self.input_queue = os.getenv("INPUT_QUEUE")
        self.output_queue = os.getenv("OUTPUT_QUEUE")
        self.fail_queue = os.getenv("FAIL_QUEUE",None)
        self.error_queue = os.getenv("ERROR_QUEUE",None)

        self.input_topic = os.getenv("INPUT_TOPIC",None)
        self.output_topic = os.getenv("OUTPUT_TOPIC",None)

        self.resolve_foreign_keys = os.getenv("RESOLVE_FK", False)
        
        # Parse INPUT_BINDINGS from environment variable (Docker Compose passes YAML lists as JSON)
        input_bindings_str = os.getenv("INPUT_BINDINGS", None)
        if input_bindings_str:
            self.input_bindings = json.loads(input_bindings_str)

        self.logger = Logger(self,log_to_console=True)

        if not self.input_queue or not (self.output_queue or self.output_topic):
            error_msg = "INPUT_QUEUE and (OUTPUT_QUEUE or OUTPUT_TOPIC) environment variables must be set."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.queue_manager = QueueManagerFactory.get_queue_manager()
        self.connect_queues()

        # Get object storage type from environment (private or public)
        object_storage_type = os.getenv("OBJECT_STORAGE_TYPE", "private").lower()
        if object_storage_type not in ["private", "public"]:
            self.logger.warning(f"Invalid OBJECT_STORAGE_TYPE '{object_storage_type}', defaulting to 'private'")
            object_storage_type = "private"

        self.object_storage_manager = ObjectStoreManagerFactory.get_object_store_manager(storage_type=object_storage_type)
        self.logger.info(f"Using {object_storage_type} object storage")

        self.document_storage_manager = DocumentStorageManagerFactory.get_document_storage_manager()
        self.data_dependencies_manager = DataDependenciesManagerFactory.get_data_dependencies_manager()


        # Initialize FK resolution helpers if enabled
        if self.resolve_foreign_keys:
            self.logger.info("FK resolution enabled for this service.")
            # Initialize PendencyManager first
            self.pendency_manager = PendencyManager(
                self.data_dependencies_manager,
                self.document_storage_manager,
                self.logger
            )
            # Initialize FKResolver with PendencyManager
            self.fk_resolver = FKResolver(
                self.data_dependencies_manager,
                self.document_storage_manager,
                self.pendency_manager,
                self.logger
            )
            # Initialize IndexManager for performance optimization
            self.index_manager = IndexManager(
                self.data_dependencies_manager,
                self.document_storage_manager,
                self.logger
            )
            # Create indexes automatically on startup (optional, controlled by env var)
            auto_create_indexes = os.getenv("AUTO_CREATE_INDEXES", "true").lower() == "true"
            if auto_create_indexes:
                self.logger.info("Auto-creating MongoDB indexes for FK resolution...")
                try:
                    # Indexes will be created lazily as data sources are loaded
                    self.logger.info("IndexManager initialized - indexes will be created as needed")
                except Exception as e:
                    self.logger.warning(f"Failed to initialize indexes: {e}")
        else:
            self.logger.info("FK resolution disabled for this service.")
            self.fk_resolver = None
            self.pendency_manager = None
            self.index_manager = None

        sentry_URL = os.getenv("URL_SENTRY")
        if sentry_URL:
            sentry_sdk.init(sentry_URL)
    def connect_queues(self):
        """
        Connect to all defined queues and exchanges.
        """
        self.logger.info("Connecting to queues...")
        self.queue_manager.connect()

        # Declare input queue
        self.queue_manager.declare_queue(self.input_queue)

        # Declare and bind input topic exchange if specified
        if self.input_topic:
            self.logger.info(f"Declaring input topic exchange: {self.input_topic}")
            self.queue_manager.declare_exchange(self.input_topic, exchange_type='topic')

            # Bind input queue to input topic with routing keys from INPUT_BINDINGS
            if self.input_bindings:
                for binding in self.input_bindings:
                    self.logger.info(f"Binding queue '{self.input_queue}' to exchange '{self.input_topic}' with routing key '{binding}'")
                    self.queue_manager.bind_queue_to_exchange(self.input_queue, self.input_topic, binding)

        # Declare output queue or output topic exchange
        if self.output_queue:
            self.queue_manager.declare_queue(self.output_queue)

        if self.output_topic:
            self.logger.info(f"Declaring output topic exchange: {self.output_topic}")
            self.queue_manager.declare_exchange(self.output_topic, exchange_type='topic')

        # Declare fail and error queues
        if self.fail_queue:
            self.queue_manager.declare_queue(self.fail_queue)
        if self.error_queue:
            self.queue_manager.declare_queue(self.error_queue)

        self.logger.info("Connected to queues and exchanges successfully.")

    def publish_output(self, message):
        """
        Publish a message to the output queue or output topic exchange.
        If output_topic is defined, publish to the exchange with the routing key.
        Otherwise, publish to the output_queue.
        """
        if self.output_topic:
            # Extract routing key from the message if available, or use a default
            try:
                msg_dict = json.loads(message) if isinstance(message, str) else message
                routing_key = msg_dict.get('routing_key')
            except:
                    self.logger.error(f"Message does not contain a routing key. Message: {message}")
                    return False
            self.queue_manager.publish_to_exchange(self.output_topic, routing_key, message)
            self.logger.info(f"Message sent to exchange '{self.output_topic}' with routing key '{routing_key}'")
        elif self.output_queue:
            self.queue_manager.publish_message(self.output_queue, message)
            self.logger.info(f"Message sent to queue '{self.output_queue}'")

    def start(self):
        """
        Start consuming messages from the input queue and handle processing.
        """
        def callback(message, acknowledge):
            self.logger.info(f"Received message: {message}")
            should_acknowledge = False
            try:
                # Process the message using the defined processing logic
                try: #transforming the message in a json object
                    json_message = json.loads(message)
                except (TypeError, ValueError) as e:
                    self.logger.error(f"Error: Unable to serialize the processor's input to JSON - {e}\n Not sending ack to this message.")
                    return False

                if self.resolve_foreign_keys:
                    if not self.retrieve_fk_data(json_message):
                        acknowledge() #remove the message from the queue because the pendency was already created in the documentDB
                        return False
                        
                json_message = self.preprocess_message(json_message)
                result = self.process_message(json_message)
                result = self.postprocess_message(result)
                #transform the result in a escaped json message
                try:
                    result = json.dumps(result,ensure_ascii=False,indent=4)
                except (TypeError, ValueError) as e:
                    self.logger.error(f"Error: Unable to serialize the processors result to JSON - {e}\n Not sending ack to this message.")
                    return False
                
                if result not in ("null",None,""): # Publish the processed message to the output queue or topic
                    try:
                        self.publish_output(result)
                    except Exception as pub_error:
                        self.logger.error(f"Failed to publish output after retries: {pub_error}")
                        # Don't acknowledge if we couldn't publish the result
                        # The message will be redelivered
                # Acknowledge the message after successful processing
                should_acknowledge = True
                try:
                    acknowledge()
                except Exception as ack_error:
                    self.logger.error(f"Failed to acknowledge message: {ack_error}")
                    # If we can't acknowledge, try to reconnect for next message
                    try:
                        self.logger.info("Reconnecting after failed acknowledgment...")
                        self.connect_queues()
                    except Exception as reconnect_error:
                        self.logger.error(f"Failed to reconnect: {reconnect_error}")
            except FailQueueException as e:
                self.logger.info(f"FailQueueException: {e}")
                fail_payload = json.dumps({"error": str(e),"original_message": message},ensure_ascii=False,indent=4)
                if self.fail_queue:
                    try:
                        self.queue_manager.publish_message(self.fail_queue, fail_payload)
                        self.logger.info(f"Failed message sent to {self.fail_queue}: {fail_payload}")
                        should_acknowledge = True
                        try:
                            acknowledge()
                        except Exception as ack_error:
                            self.logger.error(f"Failed to acknowledge message after fail queue publish: {ack_error}")
                    except Exception as pub_error:
                        self.logger.error(f"Failed to publish to fail queue: {pub_error}")
                        # Try to reconnect and publish again
                        try:
                            self.logger.info("Attempting to reconnect and publish to fail queue...")
                            self.connect_queues()
                            self.queue_manager.publish_message(self.fail_queue, fail_payload)
                            self.logger.info(f"Failed message sent to {self.fail_queue} after reconnection")
                        except Exception as reconnect_error:
                            self.logger.error(f"Failed to reconnect: {reconnect_error}")
                else:
                    raise RuntimeError(f"Message was sent to the FailQueue but it was not defined in the service.\n Message: {fail_payload}")

            except Exception as e:
                self.logger.error(f"Unhandled Exception: {e}")
                
                # Extrai informações detalhadas da exceção
                error_info = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "stacktrace": traceback.format_exc()
                }
                
                # Se for uma exceção do psycopg2 (PostgreSQL), extrair detalhes adicionais
                try:
                    import psycopg2
                    if isinstance(e, psycopg2.Error):
                        postgres_details = {}
                        
                        # pgerror: mensagem de erro completa do PostgreSQL
                        if hasattr(e, 'pgerror') and e.pgerror:
                            postgres_details["postgres_error"] = e.pgerror
                        
                        # pgcode: código de erro do PostgreSQL
                        if hasattr(e, 'pgcode') and e.pgcode:
                            postgres_details["postgres_code"] = e.pgcode
                        
                        # diag: objeto de diagnóstico com informações detalhadas
                        if hasattr(e, 'diag'):
                            diag = e.diag
                            diag_info = {}
                            
                            if hasattr(diag, 'severity') and diag.severity:
                                diag_info["severity"] = diag.severity
                            if hasattr(diag, 'sqlstate') and diag.sqlstate:
                                diag_info["sqlstate"] = diag.sqlstate
                            if hasattr(diag, 'message_primary') and diag.message_primary:
                                diag_info["message_primary"] = diag.message_primary
                            if hasattr(diag, 'message_detail') and diag.message_detail:
                                diag_info["message_detail"] = diag.message_detail
                            if hasattr(diag, 'message_hint') and diag.message_hint:
                                diag_info["message_hint"] = diag.message_hint
                            if hasattr(diag, 'statement_position') and diag.statement_position:
                                diag_info["statement_position"] = diag.statement_position
                            if hasattr(diag, 'context') and diag.context:
                                diag_info["context"] = diag.context
                            if hasattr(diag, 'schema_name') and diag.schema_name:
                                diag_info["schema_name"] = diag.schema_name
                            if hasattr(diag, 'table_name') and diag.table_name:
                                diag_info["table_name"] = diag.table_name
                            if hasattr(diag, 'column_name') and diag.column_name:
                                diag_info["column_name"] = diag.column_name
                            if hasattr(diag, 'constraint_name') and diag.constraint_name:
                                diag_info["constraint_name"] = diag.constraint_name
                            
                            if diag_info:
                                postgres_details["postgres_diagnostics"] = diag_info
                        
                        if postgres_details:
                            error_info["postgres_details"] = postgres_details
                except ImportError:
                    pass  # psycopg2 não está disponível, continua sem detalhes do PostgreSQL
                
                traceback_payload = json.dumps({
                    "error": error_info,
                    "original_message": message
                },ensure_ascii=False,indent=4)
                self.logger.error(f"Stacktrace: {traceback.format_exc()}")
                if self.error_queue:
                    try:
                        self.queue_manager.publish_message(self.error_queue, traceback_payload)
                        self.logger.error(f"Unhandled exception details sent to {self.error_queue}: {traceback_payload}")
                        should_acknowledge = True
                        try:
                            acknowledge()
                        except Exception as ack_error:
                            self.logger.error(f"Failed to acknowledge message after error queue publish: {ack_error}")
                    except Exception as pub_error:
                        self.logger.error(f"Failed to publish to error queue: {pub_error}")
                        # Try to reconnect and publish again
                        try:
                            self.logger.info("Attempting to reconnect and publish to error queue...")
                            self.connect_queues()
                            self.queue_manager.publish_message(self.error_queue, traceback_payload)
                            self.logger.error(f"Unhandled exception details sent to {self.error_queue} after reconnection")
                        except Exception as reconnect_error:
                            self.logger.error(f"Failed to reconnect and publish: {reconnect_error}")


        self.logger.info(f"Listening for messages on queue: {self.input_queue}")
        # Start consuming messages with the provided callback
        self.queue_manager.consume_messages(self.input_queue, callback)

    def close_connections(self):
        """
        Close the queue connection.
        """
        self.logger.info("Closing queue connections...")
        self.queue_manager.close_connection()
        self.logger.info("Connections closed.")

    def retrieve_fk_data(self, message):
        """
        Retrieve foreign key data from the document storage using dependency managers.

        This method:
        1. Uses DataDependenciesManager to load FK configuration
        2. Uses FKResolver to resolve FK dependencies
        3. Uses PendencyManager to resolve any pending messages

        :param message: The message being processed
        :return: Enriched message with FK raw_data_ids, or original message if no dependencies
        """
        if not self.fk_resolver or not self.pendency_manager:
            self.logger.error("Error on automatic FK resolution: FK Resolver or Pendency Manager not properly defined")
            raise Exception("Error on automatic FK resolution: FK Resolver or Pendency Manager not properly defined")

        data_source = message.get("data_source").lower()
        ###
        ### The entity_type is mandatory for automatic FK resolution, it has to be put in the message in the collector
        ###
        entity_type = message.get("entity_type").lower()

        if not data_source or not entity_type:
            self.logger.error("Error on automatic FK resolution: No data_source or entity_type in message, skipping FK resolution. Message: {message}")
            return True #when data source or entity_type is not available in the message, the message will be processed and an error will be put in the log

        # Ensure indexes exist for this data source (lazy creation)
        if self.index_manager:
            try:
                self.index_manager.ensure_fk_indexes(data_source)
            except Exception as e:
                self.logger.warning(f"Failed to ensure indexes for '{data_source}': {e}")

        # Resolve FK dependencies using FKResolver
        # If any dependencies fail, the message will not be processed (pendency(ies) created)
        all_fks_resolved = self.fk_resolver.resolve_fk_dependencies(message)

        if not all_fks_resolved:
            # Message has unresolved FKs - pendency(ies) were created, don't process further
            self.logger.info(f"Message {message.get('raw_data_id')} has unresolved FKs, one or more pendencies were created")
            return False

        # All FKs resolved - check for and resolve any pendencies that depend on this record
        # This will merge pending message fields into the current message
        # Use recursive resolution to handle cascading pendencies
        resolved_pendencies = self.pendency_manager.resolve_pendencies_recursive(
            data_source,
            entity_type,
            message
        )
        self.logger.debug(f"Resolved {resolved_pendencies} pendencies for {message.get('raw_data_id')}")

        return True

    def preprocess_message(self, message):
        """
        Preprocess the message (logic specific to the service).
        """
        # Example placeholder logic for sending the message to fail queue
        #raise FailQueueException("Message contains 'fail', routing to fail queue.")
        return message

    @abstractmethod
    def process_message(self, message):
        """
        Process the message (logic specific to the service).
        """
        # Example placeholder logic for sending the message to fail queue
        #raise FailQueueException("Message contains 'fail', routing to fail queue.")
        pass


    def postprocess_message(self, message):
        """
        Postprocess the message (logic specific to the service).
        """
        # Example placeholder logic for sending the message to fail queue
        #raise FailQueueException("Message contains 'fail', routing to fail queue.")
        return message