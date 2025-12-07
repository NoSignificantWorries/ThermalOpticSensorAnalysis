import os
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict

import clickhouse_connect as clk
from dotenv import load_dotenv


class ClickhouseConnect:
    def __init__(self, env_pathes: list[str]) -> None:
        for env_file in env_pathes:
            dotenv_path = Path(env_file).absolute().resolve()
            load_dotenv(dotenv_path)

        self.config = {
            "user": os.getenv("CLICKHOUSE_USER"),
            "pass": os.getenv("CLICKHOUSE_PASSWORD"),
            "host": os.getenv("CLICKHOUSE_HOST"),
            "port": int(os.getenv("CLICKHOUSE_PORT", 8123)),
            "database": os.getenv("CLICKHOUSE_DB")
        }
        self._client = None
        self._connect()

    def _connect(self):
        try:
            self._client = clk.get_client(host=self.config["host"],
                                         username=self.config["user"],
                                         password=self.config["pass"],
                                         database=self.config["database"],
                                         port=self.config["port"])
            self._client.query('SELECT 1')
        except Exception as err:
            print(f"[ERROR]: {err}")
            self._client = None
            raise

    @contextmanager
    def get_connection(self):
        try:
            yield self._client
        except Exception as e:
            print(f"[ERROR]: {e}")
            raise

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List:
        with self.get_connection() as client:
            result = client.query(query, parameters=params)
            return result.result_rows
    
    def insert_data(self, table: str, data: List[List], column_names: List[str]):
        with self.get_connection() as client:
            client.insert(table, data, column_names=column_names)

    def close(self):
        if self._client:
            self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            self._client.close()

