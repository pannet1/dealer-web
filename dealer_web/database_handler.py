from __future__ import annotations
import sqlite3
from typing import Optional, Dict, Any, List, Tuple


class DatabaseHandler:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self.connection: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None

    def connect(self) -> None:
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to the database: {e}")

    def disconnect(self) -> None:
        try:
            if self.connection:
                self.connection.close()
        except sqlite3.Error as e:
            print(f"Error disconnecting from the database: {e}")

    def execute_query(self,
                      query: str,
                      params: Optional[Tuple[Any, ...]] = None
                      ) -> None:
        try:
            if self.cursor:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)

                self.connection.commit()
        except sqlite3.Error as e:
            print(f"Error executing query: {e}")

    def fetch_data(self,
                   query: str,
                   params: Optional[Tuple[Any, ...]] = None
                   ) -> List[Tuple[Any, ...]]:
        try:
            if self.cursor:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)

                return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")
            return []

    def create_table(self, table_name: str, columns: List[str]) -> None:
        try:
            query = f"CREATE TABLE IF NOT EXISTS {table_name} \
            ({', '.join(columns)})"
            self.execute_query(query)
        except sqlite3.Error as e:
            print(f"Error creating table: {e}")

    def insert_data(self, table_name: str, data: Dict[str, Any]) -> None:
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            query = f"INSERT INTO {table_name} ({columns}) \
            VALUES ({placeholders})"
            self.execute_query(query, tuple(data.values()))
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")
