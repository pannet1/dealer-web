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

    def drop_table(self, table_name: str) -> None:
        try:
            query = f"DROP TABLE IF EXISTS {table_name}"
            self.execute_query(query)
        except sqlite3.Error as e:
            print(f"Error dropping table: {e}")


if __name__ == "__main__":
    # Create an instance of the DatabaseHandler
    handler = DatabaseHandler("spread.db")

    # Connect to the database
    handler.connect()
    handler.drop_table("spread")
    # Create the "spread" table
    handler.create_table("spread", ["id INTEGER PRIMARY KEY", "userid TEXT", "name TEXT", "mtm INTEGER",
                         "tp INTEGER", "sl INTEGER", "trail_after INTEGER", "trail_at INTEGER", "status INTEGER"])

    # Insert sample data into the "spread" table
    spread_data = {
        "id": 1,
        "userid": "user1",
        "name": "Sample Spread",
        "mtm": 100,
        "tp": 10,
        "sl": 5,
        "trail_after": 20,
        "trail_at": 15,
        "status": 1}
    handler.insert_data("spread", spread_data)

    handler.drop_table("items")
    # Create the "items" table
    handler.create_table("items", ["id INTEGER PRIMARY KEY", "spread_id INTEGER", "instrument TEXT",
                         "exchange TEXT", "entry REAL", "side INTEGER", "quantity INTEGER", "mtm INTEGER", "ltp REAL"])

    items_data = {
        "id": 1,
        "spread_id": 1,
        "instrument": "STOCK CE",
        "exchange": "NFO",
        "entry": 100,
        "side": 1,
        "quantity": 25,
        "mtm": 10,
        "ltp": 105.5
    }
    handler.insert_data("items", items_data)

    items_data = {
        "id": 2,
        "spread_id": 1,
        "instrument": "Stock PE",
        "exchange": "NFO",
        "entry": 100,
        "side": -1,
        "quantity": 25,
        "mtm": 10,
        "ltp": 105.5
    }
    handler.insert_data("items", items_data)

    query = """
        SELECT items.*
        FROM items
        INNER JOIN spread ON items.spread_id = spread.id
        WHERE spread.id = ?
    """
    spread_id = 1  # The related spread_id to filter items
    items = handler.fetch_data(query, (spread_id,))

    # Print the retrieved items
    for item in items:
        print(item)
    # Disconnect from the database
    handler.disconnect()
