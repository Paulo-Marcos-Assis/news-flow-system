import os
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from service_essentials.relational_storage.relational_storage_manager import RelationalStorageManager
from service_essentials.utils.logger import Logger


class PostgreSQLManager(RelationalStorageManager):
    """
    Implementation of the Relational Storage Manager for PostgreSQL.
    """
    
    def __init__(self):
        self.connection = None
        self.logger = Logger(None, log_to_console=True)
        self.connect()

    def connect(self, **kwargs):
        """
        Connect to PostgreSQL database.
        
        :param kwargs: Optional connection parameters. If not provided, uses environment variables.
        """
        try:
            # Use provided parameters or fall back to environment variables
            db_config = {
                "dbname": os.getenv("DATABASE_PG"),
                "user": os.getenv("USERNAME_PG"),
                "password": os.getenv("SENHA_PG"),
                "host": os.getenv("HOST_PG"),
                "port": os.getenv("PORT_PG")
            }
            
            self.connection = psycopg2.connect(**db_config)
        except psycopg2.Error as e:
            self.logger.error(f"Falha crítica ao conectar com o PostgreSQL: {e}")
            self.connection = None
            raise ConnectionError(f"Failed to connect to PostgreSQL: {e}")

    def get_connection(self):
        """
        Get the current database connection.
        
        :return: psycopg2 connection object
        """
        if not self.is_connected():
            self.logger.warning("Conexão com o PostgreSQL perdida. Tentando reconectar...")
            self.connect()
        return self.connection

    def get_cursor(self, **kwargs):
        """
        Get a database cursor for executing queries.
        
        :param kwargs: Optional cursor parameters (e.g., cursor_factory=RealDictCursor)
        :return: Database cursor object
        """
        connection = self.get_connection()
        if connection:
            return connection.cursor(**kwargs)
        else:
            self.logger.error("Não foi possível obter cursor: conexão com PostgreSQL não disponível")
            return None

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch: bool = False) -> Optional[Any]:
        """
        Execute a SQL query.
        
        :param query: SQL query string
        :param params: Query parameters
        :param fetch: Whether to fetch results
        :return: Query results if fetch=True, None otherwise
        """
        cursor = self.get_cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch:
                return cursor.fetchall()
            return None
        except psycopg2.Error as e:
            self.logger.error(f"Erro ao executar query no PostgreSQL: {e}\nQuery: {query[:200]}...")
            raise
        finally:
            cursor.close()

    def execute_many(self, query: str, params_list: List[tuple]):
        """
        Execute a SQL query with multiple parameter sets.
        
        :param query: SQL query string
        :param params_list: List of parameter tuples
        """
        cursor = self.get_cursor()
        try:
            cursor.executemany(query, params_list)
        except psycopg2.Error as e:
            self.logger.error(f"Erro ao executar query em lote no PostgreSQL: {e}\nQuery: {query[:200]}...")
            raise
        finally:
            cursor.close()

    def commit(self):
        """
        Commit the current transaction.
        """
        if self.connection:
            try:
                self.connection.commit()
            except psycopg2.Error as e:
                self.logger.error(f"Erro ao fazer commit da transação PostgreSQL: {e}")
                raise
        else:
            self.logger.warning("Tentativa de commit sem conexão ativa com PostgreSQL")

    def rollback(self):
        """
        Rollback the current transaction.
        """
        if self.connection and not self.connection.closed:
            try:
                self.connection.rollback()
                self.logger.warning("Rollback executado na transação PostgreSQL")
            except psycopg2.Error as e:
                self.logger.error(f"Erro ao fazer rollback da transação PostgreSQL: {e}")
                raise
        else:
            if self.connection and self.connection.closed:
                self.logger.warning("Tentativa de rollback em conexão já fechada com PostgreSQL")
            else:
                self.logger.warning("Tentativa de rollback sem conexão ativa com PostgreSQL")

    def close_connection(self):
        """
        Close the connection to the PostgreSQL database.
        """
        if self.connection and not self.connection.closed:
            self.connection.close()

    def is_connected(self) -> bool:
        """
        Check if the database connection is active.
        
        :return: True if connected, False otherwise
        """
        return self.connection is not None and not self.connection.closed
