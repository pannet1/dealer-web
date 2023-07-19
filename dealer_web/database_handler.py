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
    handler.connect()
    handler.drop_table("spread")
    handler.drop_table("items")
    # Create the "spread" table
    handler.create_table("spread", ["id INTEGER PRIMARY KEY", "userid TEXT",
                                    "name TEXT", "mtm INTEGER", "tp INTEGER",
                                    "sl INTEGER", "trail_after INTEGER",
                                    "trail_at INTEGER", "status INTEGER",
                                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"])    # Insert sample data into the "spread" table
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
    # Create the "items" table
    handler.create_table("items", ["id INTEGER PRIMARY KEY",
                                   "spread_id INTEGER", "instrument TEXT",
                                   "exchange TEXT", "entry REAL",
                                   "side INTEGER", "quantity INTEGER",
                                   "mtm INTEGER", "ltp REAL"])
    # Create the "items" update_mtm_trigger
    query = """
        CREATE TRIGGER update_mtm_trigger
        AFTER UPDATE OF ltp ON items
        FOR EACH ROW
        BEGIN
            UPDATE items
            SET mtm = (NEW.side * NEW.entry) + (-1 * NEW.side * NEW.ltp)
            WHERE id = NEW.id;
        END;
    """
    handler.execute_query(query)
    items_data = {
        "id": 1,
        "spread_id": 1,
        "instrument": "STOCKCE",
        "exchange": "NFO",
        "entry": 90,
        "side": 1,
        "quantity": 25,
        "mtm": 0,
        "ltp": 10.5
    }
    handler.insert_data("items", items_data)
    items_data = {
        "id": 2,
        "spread_id": 1,
        "instrument": "BANKNIFTY23-AUG-12",
        "exchange": "NFO",
        "entry": 100,
        "side": -1,
        "quantity": 25,
        "mtm": 0,
        "ltp": 20.5
    }
    handler.insert_data("items", items_data)

    query = """
        SELECT items.*
        FROM items
        INNER JOIN spread ON items.spread_id = spread.id
    """
    items = handler.fetch_data(query, )

    # Print the retrieved items
    for item in items:
        print(item)

    updated_item = {
        "instrument": "STOCKCE",
        "ltp": 150.0  # Updated ltp value
    }
    # Update the row, excluding the 'mtm' field
    query = """
        UPDATE items
        SET ltp = :ltp
        WHERE instrument = :instrument
    """
    handler.execute_query(query, updated_item)

    # Fetch the updated data from the "items" table
    query = "SELECT * FROM items"
    updated_items = handler.fetch_data(query, )

    # Print the updated item
    for item in updated_items:
        print(item)

    # Disconnect from the database
    handler.disconnect()
