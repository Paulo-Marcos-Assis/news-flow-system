from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService

class ProcessorTeste(BasicProducerConsumerService):
    def __init__(self):
        super().__init__()
        
    def process_message(self, record):
        self.retrieve_fk_data(record)
        return record


if __name__ == '__main__':
    processor = ProcessorTeste()
    processor.start()