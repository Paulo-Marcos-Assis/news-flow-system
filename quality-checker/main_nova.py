import importlib
import os
import json
from checkers.base_quali_checker import BaseQualiChecker
from utils.date_checker import DateChecker

from service_essentials.exceptions.fail_queue_exception import FailQueueException
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


import re
import math

class QualityChecker(BasicProducerConsumerService):
    
    def is_number_string(self, s: str) -> bool:
        s = s.strip()
        if s.lower() == "nan" or s == "":
            return False
        return bool(re.fullmatch(r"-?\d+(\.\d+)?", s))

    def convert_numbers(self, obj):
        if isinstance(obj, dict):
            return {k: self.convert_numbers(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numbers(item) for item in obj]
        else:
            if obj is None:
                return None
            if isinstance(obj, (int, float)):
                if isinstance(obj, float) and math.isnan(obj):
                    return None
                return int(obj)
            if isinstance(obj, str):
                if obj.strip() == "":  
                    return None
                if obj.lower() == "nan":
                    return None
                if self.is_number_string(obj):
                    return int(float(obj))
                return obj
            return obj

    def process_message(self, record):
        failures = {}
        # record = self.convert_numbers(record)   


        # Recebe os campos de verificação divididos em 'structured' e 'non_structured'
        with open('fields.json', 'r') as file:
            config = json.load(file)
        
        fields = config['structured'] + config['non_structured']
        
        for checker in self.load_checkers().values():
            if checker.check_name in fields:
                self.logger.info(f"Applying quality check {checker.check_name}")
                checked,msg = checker.check(record)
                if not checked:
                    failures[checker.check_name] = msg

        if failures:
            raise FailQueueException(failures)

        return record

    def load_checkers(self):
        path = "checkers"
        checkers = {}
        for directory in os.scandir(path):
            if directory.is_dir() and directory.name != "utils":
                for file in os.listdir(directory.path):
                    if file.endswith(".py") and file != "__init__.py":
                        module_name = f"{directory.path.replace('/', '.')}.{file[:-3]}"
                        module = importlib.import_module(module_name)
                        for attr in dir(module):
                            cls = getattr(module, attr)
                            if isinstance(cls, type) and issubclass(cls, BaseQualiChecker) and cls is not BaseQualiChecker and cls is not DateChecker:
                                checkers[cls.check_name] = cls(self.logger)
        return checkers

if __name__ == '__main__':
    processor = QualityChecker()
    processor.start()