import json
from math import log
import os
from pymongo import MongoClient

from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService
from service_essentials.mongodb_ingestor.mongo_ingestor import MongoDBIngestor

class SplitterDom(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        self.mongo = MongoDBIngestor("DOM")

    def process_message(self, message):
        self.object_storage_manager.download_file(message["bucket"],message["result_file"],message["result_file"])
        with open(message["result_file"], "r", encoding="utf-8") as json_file:
            try:
                data = json.load(json_file)
                for i,licitacao in enumerate(data):
                    
                    universal_id = self.mongo.ingest_json(licitacao)
                    licitacao["raw_data_id"] = str(universal_id)
                    licitacao["data_source"] = "dom"
                    self.queue_manager.publish_message(self.output_queue, json.dumps(licitacao))
                self.object_storage_manager.delete_file(message["bucket"],message["result_file"])
                os.remove(message["result_file"])
            except json.JSONDecodeError as e:
                raise ValueError(f"Erro ao decodificar o arquivo JSON: {e}")
        return None 

if __name__ == '__main__':
    processor = SplitterDom()
    processor.start()