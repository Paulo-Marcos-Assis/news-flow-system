import importlib
import os

from verifiers.base_verifier import BaseVerifier

from service_essentials.exceptions.fail_queue_exception import FailQueueException
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService

from utils.get_fields_verify import GetFieldsVerify


class VerifierDom(BasicProducerConsumerService):
    
    def process_message(self, record):
        failures = {}

        for table in record['extracted']:

            table_fields = GetFieldsVerify.get_fields_verify(table)

            if not table_fields:
                continue

            verifiers = self.load_verifiers(table, table_fields)

            for field_name, verifier in verifiers.items():
                if field_name in table_fields:
                    self.logger.info(f"Applying verification {field_name}")
                    verified, msg = verifier.verify(record)

                    if not verified:
                        failures[field_name] = msg

        if failures:
            raise FailQueueException(failures)

        result = record["extracted"]
        result["raw_data_id"] = record["raw_data_id"]
        result["data_source"] = record["data_source"]

        return result

    def load_verifiers(self, table, fields):

        verifiers = {}
        path = f"verifiers.{table}"

        for field in fields:
            module_name = f"{path}.{field}_verifier"
            module = importlib.import_module(module_name)
            for attr in dir(module):
                cls = getattr(module, attr)
                if isinstance(cls, type) and issubclass(cls, BaseVerifier) and cls is not BaseVerifier:
                    verifiers[cls.verification_name] = cls(self.logger)

        return verifiers

if __name__ == '__main__':
    processor = VerifierDom()
    processor.start()
    
