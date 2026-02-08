'''' 
Cliente básico PostgreSQL 
'''

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Result

# from typing import Optional, Dict, Any, List, Union
import logging

class PostgreSqlClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        banco: str,
    ):
        self.base_url = (
            f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{banco}"
        )
        self.engine: Engine = create_engine(self.base_url)

    def execute_command(self, command: str, params=None, fetch: bool = True):

        try:
            with self.engine.begin() as conn:
                if isinstance(params, list):
                    result: Result = conn.execute(text(command), params)
                else:
                    result: Result = conn.execute(text(command), params or {})
                if fetch:
                    try:
                        return [dict(row._mapping) for row in result]
                    except Exception as e:
                        print(e)
                        return []
                return result.rowcount
        except Exception as e:
            logging.exception("Error executing sql command")
            raise e

    def add_data(self, table_name: str, schema_name: str, data: list[dict]):
        try:
            table_schema = self.get_schema(table_name, schema_name)
            if not table_schema:
                raise Exception(
                    f"Table schema not found for {schema_name}.{table_name}"
                )

            columns = list(data[0].keys())
            columns_str = ", ".join(columns)
            placeholders = ", ".join([f":{col}" for col in columns])
            command = f'INSERT INTO "{schema_name}"."{table_name}" ({columns_str}) VALUES ({placeholders})'
            print(command)

            data_filter = [
                {k: v for k, v in linha.items() if k in columns} for linha in data
            ]

            return self.execute_command(command, data_filter)

        except Exception as e:
            logging.exception("Error adding data:")
            raise e

    def get_schema(self, table_name: str, schema_name: str = "public"):
        result = self.execute_command(
            "SELECT * FROM schema_dinamico(:nome_tabela, :nome_schema)",
            {"nome_tabela": table_name, "nome_schema": schema_name},
        )
        return result
