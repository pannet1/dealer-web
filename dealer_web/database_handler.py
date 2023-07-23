from __future__ import annotations
import sqlite3
from typing import Optional, Dict, Any, List, Tuple


class DatabaseHandler:
    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()

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

    def fetch_data(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        try:
            if self.cursor:
                if params:
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)

                # Get the column names from the cursor description
                column_names = [column[0]
                                for column in self.cursor.description]

                # Fetch rows and convert each row into a dictionary
                rows = self.cursor.fetchall()
                result = [dict(zip(column_names, row)) for row in rows]
                return result
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
    # Before creating the triggers, set the recursive_triggers pragma to ON
    handler.drop_table("spread")
    handler.drop_table("items")

    """
    create tables
    """
    handler.create_table("spread", ["id INTEGER PRIMARY KEY",
                                    "name TEXT", "mtm INTEGER", "tp INTEGER",
                                    "sl INTEGER", "trail_after INTEGER",
                                    "trail_at INTEGER", "status INTEGER",
                                    "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"])    # Insert sample data into the "spread" table
    # Create the "items" table
    handler.create_table("items", ["id INTEGER PRIMARY KEY",
                                   "spread_id INTEGER", "instrument TEXT",
                                   "exchange TEXT", "entry REAL",
                                   "side INTEGER", "quantity INTEGER",
                                   "mtm INTEGER", "ltp REAL"])
    """
    TRIGGERS NOT USED FOR NOW

    query = 'CREATE TRIGGER update_mtm_trigger
    AFTER UPDATE OF ltp ON items
    FOR EACH ROW
    BEGIN
    UPDATE items
    SET mtm = (NEW.side * (NEW.ltp - NEW.entry)) * NEW.quantity
    WHERE id = NEW.id
    END'
    handler.execute_query(query)

      INSERT DATA 
    """
    spread_data_1 = {
        "name": "First Spread",
        "mtm": 100,
        "tp": 10,
        "sl": 5,
        "trail_after": 20,
        "trail_at": 15,
        "status": 1}
    spread_data_2 = {
        "name": "Sample Spread 2",
        "mtm": 100,
        "tp": 10,
        "sl": 5,
        "trail_after": 20,
        "trail_at": 15,
        "status": 1}
    handler.insert_data("spread", spread_data_1)
    handler.insert_data("spread", spread_data_2)

    items_data_1 = {
        "spread_id": 1,
        "instrument": "PEL27JUL23920PE",
        "exchange": "NFO",
        "entry": 100,
        "side": 1,
        "quantity": 300,
        "mtm": -100,
        "ltp": 101
    }
    items_data_2 = {
        "spread_id": 1,
        "instrument": "ACC27JUL231840CE",
        "exchange": "NFO",
        "entry": 100,
        "side": -1,
        "quantity": 1500,
        "mtm": 100,
        "ltp": 20.5
    }
    handler.insert_data("items", items_data_1)
    handler.insert_data("items", items_data_2)

    query = """
        SELECT items.*
        FROM items
        INNER JOIN spread ON items.spread_id = spread.id
    """
    items = handler.fetch_data(query, )

    for item in items:
        print(item)

    """
    UPDATE
    """
    updated_item_1 = {
        "instrument": "ACC27JUL231840CE",
        "ltp": 101  # Updated ltp value
    }
    updated_item_2 = {
        "instrument": "PEL27JUL23920PE",
        "ltp": 101  # Updated ltp value
    }
    # Update the row, excluding the 'mtm' field
    query = """
        UPDATE items
        SET ltp = :ltp
        WHERE instrument = :instrument
    """
    handler.execute_query(query, updated_item_1)
    handler.execute_query(query, updated_item_2)

    # Fetch the updated data from the "items" table
    query = "SELECT * FROM items"
    updated_items = handler.fetch_data(query, )

    query = """
        SELECT spread.*
        FROM spread
        where status >= 0
    """
    spreads = handler.fetch_data(query, )

    # Print the retrieved items
    for spread in spreads:
        print(spread)
    # Print the updated item
    for item in updated_items:
        print(item)
    # Disconnect from the database
    handler.disconnect()
