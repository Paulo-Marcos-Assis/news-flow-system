from abc import ABC, abstractmethod
from service_essentials.relational_storage.relational_storage_manager_factory import RelationalStorageManagerFactory
from typing import Any, List, Optional
from dateutil import parser
import requests
import json
import unicodedata
import hashlib

class BaseQualiChecker(ABC):
    check_name = "base"
    table_name = None
    """Base class for all verifiers."""
    
    # Conexão compartilhada entre todas as instâncias (class variable)
    _shared_db_manager = None
    
    def __init__(self,logger):
        self.logger = logger
        self._query_cache = {}  # Cache para queries repetidas
        
        # Inicializa conexão compartilhada se ainda não existe
        if BaseQualiChecker._shared_db_manager is None:
            BaseQualiChecker._shared_db_manager = RelationalStorageManagerFactory.get_relational_storage_manager()
            logger.info("Conexão compartilhada de banco inicializada para checkers")
        
    @abstractmethod
    def check(self, record):
        raise NotImplementedError("Subclasses must implement this method.")
    
    def execute_db_query(self, query: str, params: Optional[tuple] = None, use_cache: bool = True) -> tuple:
        """
        Returns tuple: (success: bool, rows: list or None, error: str or None, executed_query: str)
        """
        # Build the executed query string for error reporting
        executed_query = query
        if params:
            try:
                executed_query = query % tuple(f"'{p}'" if isinstance(p, str) else str(p) for p in params)
            except:
                executed_query = f"{query} -- params: {params}"
        
        # Gera chave de cache baseada na query e parâmetros
        if use_cache:
            cache_key = hashlib.md5(f"{query}:{params}".encode()).hexdigest()
            if cache_key in self._query_cache:
                return (True, self._query_cache[cache_key], None, executed_query)
        
        try:
            # Usa conexão compartilhada ao invés de criar nova a cada query
            results = BaseQualiChecker._shared_db_manager.execute_query(query, params=params, fetch=True)
            
            # Armazena no cache se habilitado
            if use_cache:
                self._query_cache[cache_key] = results
            
            return (True, results, None, executed_query)
        except Exception as er:
            self.logger.error(f"Erro executando query no database: {er}")
            self.logger.error(f"Query: {query}")
            self.logger.error(f"Params: {params}")
            
            # Rollback da transação para evitar "operation aborted" em queries subsequentes
            try:
                self.logger.warning("Executando rollback da transação após erro")
                BaseQualiChecker._shared_db_manager.rollback()
            except Exception as rollback_err:
                self.logger.error(f"Erro ao fazer rollback: {rollback_err}")
            
            return (False, None, str(er), executed_query)

    def normalize_string(self, text: str) -> str:
        return ''.join(
                    c for c in unicodedata.normalize('NFKD', text)
                    if not unicodedata.combining(c)
                ).lower()
        
    def is_valid_integer(self, num_str: str) -> bool:
        INT_MAX = 2147483647
        INT_MIN = -2147483648

        try:
            num_str = int(num_str)
        except ValueError:
            return False

        return INT_MIN <= num_str <= INT_MAX
    
    def is_valid_bigint(self, num_str: str) -> bool:
        INT_MAX = 9223372036854775807
        INT_MIN = -9223372036854775808

        try:
            num_str = int(num_str)
        except ValueError:
            return False

        return INT_MIN <= num_str <= INT_MAX
    
    def is_valid_smallint(self, num_str: str) -> bool:
        INT_MAX = 32767
        INT_MIN = -32768

        try:
            num_str = int(num_str)
        except ValueError:
            return False

        return INT_MIN <= num_str <= INT_MAX
            
    
    def is_double(self, num_str) -> bool:
        try:
            # Replace comma with dot for decimal separator
            if isinstance(num_str, str):
                num_str = num_str.replace(',', '.')
            # tenta converter a string recebida em ponto flutuante
            float(num_str)
        except ValueError:
            return False
        
        return True
    
    def is_varchar(self, data_str, size: int) -> bool:
        if not isinstance(data_str, str):
            data_str = str(data_str)
            
        return len(data_str) <= size
    
    def is_bool(self, bool_str) -> bool:
        BOOL_VALUES = {'true', 't', 'yes', 'y', 'on', '1', 'false', 'f', 'no', 'n', 'off', '0'}

        if isinstance(bool_str, bool):
            return True

        # Garante a manipulação de uma String
        bool_str = str(bool_str)
        bool_str = bool_str.lower()

        return bool_str in BOOL_VALUES