import json
import os
import shutil
import logging
from typing import Any, Dict

from service_essentials.basic_service.basic_producer_consumer_service import (
    BasicProducerConsumerService,
)
from service_essentials.mongodb_ingestor.mongo_ingestor import MongoDBIngestor

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SplitterPncp(BasicProducerConsumerService):
    """
    A service to split a JSON file of bids into individual messages.

    This service consumes a message indicating a file in object storage,
    downloads it, reads the bids within it, and publishes each bid to a
    queue for further processing. It also ingests each bid into MongoDB.
    """

    def __init__(self):
        """
        Initializes the PncpSplitter service and the MongoDB ingestor.
        """
        super().__init__()
        self.mongo = MongoDBIngestor("pncp")

    def delete_temp_directory(self, directory_path: str) -> None:
        """
        Deletes a directory and its contents if it exists.

        Args:
            directory_path (str): The path to the directory to delete.
        """
        if os.path.exists(directory_path):
            shutil.rmtree(directory_path)
            logger.info(f"Successfully deleted temporary directory: {directory_path}")

    def process_message(self, message: Dict[str, Any]) -> None:
        """
        Processes a message to split a file of bids.

        Downloads the file, iterates through the bids, publishes each one
        to the output queue, ingests it into MongoDB, and then cleans up
        the local and remote files.

        Args:
            message (Dict[str, Any]): The message containing the bucket and file path.
        """
        file_path = message["result_file"]
        bucket_name = message["bucket"]
        # Get entity_type from the collector's message
        entity_type = message.get("entity_type")
        
        if not entity_type:
            logger.error(f"Message from collector is missing 'entity_type': {message}")
            raise ValueError("Cannot process message from collector without 'entity_type'")

        temp_base_dir = None

        try:
            self.object_storage_manager.download_file(bucket_name, file_path, file_path)
            logger.info(f"Successfully downloaded {file_path} from bucket {bucket_name}.")

            with open(file_path, "r", encoding="utf-8") as json_file:
                try:
                    data = json.load(json_file)
                    logger.info(f"Loaded {len(data)} records from {file_path}.")
                    for bid in data:
                        # Add entity_type to the record BEFORE it's used by any other process
                        bid["entity_type"] = entity_type

                        universal_id = self.mongo.ingest_json(bid)
                        bid["raw_data_id"] = str(universal_id)
                        bid["data_source"] = "PNCP"
                        
                        bid_message = json.dumps(bid)
                        self.queue_manager.publish_message(self.output_queue, bid_message)
                    logger.info(f"Finished processing and publishing {len(data)} records.")

                    self.object_storage_manager.delete_file(bucket_name, file_path)
                    logger.info(f"Deleted {file_path} from bucket {bucket_name}.")

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON from file {file_path}: {e}")
                    # Re-raising the exception to potentially trigger error-handling logic in the base service.
                    raise ValueError(f"Error decoding JSON file: {e}")
        finally:
            # Ensure local cleanup happens even if processing fails.
            # The logic assumes a path structure like 'modality/year/month/day/file.json'
            # and aims to delete the top-level 'modality' directory.
            if os.path.exists(file_path):
                temp_directory = os.path.dirname(file_path)
                if temp_directory:
                    temp_base_dir = temp_directory.split('/')[0]
                    self.delete_temp_directory(temp_base_dir)


if __name__ == '__main__':
    processor = SplitterPncp()
    processor.start()
