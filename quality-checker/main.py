import importlib
import os
import json
import inspect
from checkers.base_quali_checker import BaseQualiChecker
from checkers.base_nested_checker import BaseNestedChecker

from service_essentials.exceptions.fail_queue_exception import FailQueueException
from service_essentials.basic_service.basic_producer_consumer_service import BasicProducerConsumerService


import re
import math

class QualityChecker(BasicProducerConsumerService):
    
    def __init__(self):
        super().__init__()
        # Carrega checkers e configurações uma única vez na inicialização
        self.checkers = self._load_checkers()
        self.tables = self._load_tables()
        self.fields = self._build_fields_list()
        self.logger.info(f"Quality Checker inicializado com {len(self.checkers)} checkers")
    
    def _load_tables(self):
        """Carrega tables.json uma única vez"""
        with open('tables.json', 'r') as file:
            return json.load(file)
    
    def _build_fields_list(self):
        """Constrói lista de campos uma única vez"""
        return (
            self.tables['banco_de_precos'] 
            + self.tables['cnae']
            + self.tables['documento']
            + self.tables['empenho']
            + self.tables['ente']
            + self.tables['inidonea']
            + self.tables['item_licitacao']
            + self.tables['item_nfe'] 
            + self.tables['liquidacao']
            + self.tables['modalidade_licitacao']
            + self.tables['motivo_situacao_cadastral']
            + self.tables['municipio']
            + self.tables['natureza_juridica']
            + self.tables['nfe'] 
            + self.tables['noticia']
            + self.tables['pagamento_empenho']
            + self.tables['pessoa']
            + self.tables['pessoa_fisica']
            + self.tables['pessoa_juridica']
            + self.tables['processo_licitatorio']
            + self.tables['situacao_cadastral']
            + self.tables['tipo_cotacao']
            + self.tables['tipo_documento']
            + self.tables['tipo_especificacao_ug']
            + self.tables['tipo_licitacao']
            + self.tables['tipo_objeto_licitacao']
            + self.tables['tipo_ug']
            + self.tables['unidade_gestora']
            + self.tables['unidade_orcamentaria']
        )
    
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
        

        # # Verifica quais tabelas estão presentes no record
        # relevant_checkers = set()
        # for table_name in record.keys():
        #     if table_name in self.tables:
        #         # Adiciona todos os checkers dessa tabela
        #         relevant_checkers.update(self.tables[table_name])
        
        # # Executa apenas os checkers relevantes
        # for checker_name in relevant_checkers:
        #     if checker_name in self.checkers:
        #         checker = self.checkers[checker_name]
        #         self.logger.info(f"Applying quality check {checker_name}")
        #         check_results = checker.check(record)
        #         if not isinstance(check_results, list):
        #             check_results = [check_results]
                
        #         for results in check_results:
        #             checked, msg = results
        #             if not checked:
        #                 failures[checker_name] = msg

        for table_name in record.keys():
            if table_name in self.checkers:
                for checker_name, checker in self.checkers[table_name].items():
                    self.logger.info(f"Applying quality check {checker_name}")
                    check_results = checker.check(record)
                    if not isinstance(check_results, list):
                        check_results = [check_results]
                    
                    for results in check_results:
                        checked, msg = results
                        if not checked:
                            failures[checker_name] = msg

                        


        if failures:
            raise FailQueueException(failures)

        return record

    def _load_checkers(self):
        """Carrega todos os checkers uma única vez na inicialização"""
        path = "checkers"
        checkers = {}
        nested_checkers = []
        for directory in os.scandir(path):
            if directory.is_dir():
                for file in os.listdir(directory.path):
                    if file.endswith(".py") and file != "__init__.py":
                        module_name = f"{directory.path.replace('/', '.')}.{file[:-3]}"
                        module = importlib.import_module(module_name)
                        for attr in dir(module):
                            cls = getattr(module, attr)
                            if isinstance(cls, type) and issubclass(cls, BaseQualiChecker) and not inspect.isabstract(cls):
                                if issubclass(cls, BaseNestedChecker):
                                    nested_checkers.append((cls.table_name, cls.check_name, cls))
                                else:
                                    checkers.setdefault(cls.table_name, {})
                                    checkers[cls.table_name][cls.check_name] = cls(self.logger)
        
        for table, field, cls in nested_checkers:
            checkers.setdefault(table, {})
            checkers[table][field] = cls(self.logger, checkers)

        # Debug: log loaded checkers by scope
        for scope, scope_checkers in checkers.items():
            self.logger.info(f"[LOAD] Scope '{scope}': {list(scope_checkers.keys())}")

        return checkers

if __name__ == '__main__':
    processor = QualityChecker()
    processor.start()
