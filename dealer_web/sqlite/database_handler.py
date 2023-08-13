from __future__ import annotations
import sqlite3
from typing import Optional, Dict, Any, List, Tuple, Union
from toolkit.fileutils import Fileutils


class DatabaseHandler:
    def __init__(self, db_name: str) -> None:
        mtime = Fileutils().get_file_mtime(db_name)
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        if mtime == "file_not_found":
            self.create_table("spread",
                              ["id INTEGER PRIMARY KEY",
                               "name TEXT", "capital INTEGER",
                               "mtm INTEGER", "tp INTEGER",
                               "sl INTEGER", "max_mtm INTEGER",
                               "trail_after INTEGER",
                               "trail_at INTEGER", "status INTEGER",
                               "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"])
            self.create_table("items",
                              ["id INTEGER PRIMARY KEY",
                               "spread_id TEXT", "symbol TEXT",
                               "exchange TEXT", "entry REAL",
                               "side INTEGER", "quantity INTEGER",
                               "mtm INTEGER", "ltp REAL"])
            self.create_table("user",
                              ["id INTEGER PRIMARY KEY",
                               "user TEXT"])
            self.create_table("spread_user",
                              ["id INTEGER PRIMARY KEY",
                               "spread_id INTEGER",
                               "user_id INTEGER"])

    def disconnect(self) -> None:
        try:
            if self.connection:
                self.connection.close()
        except sqlite3.Error as e:
            print(f"Error disconnecting from the database: {e}")

    def execute_query(self,
                      query: str,
                      params: Optional[Tuple[Any, Any]] = None
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

    def fetch_data(
        self, query: str,
        params: Optional[Tuple[Any, ...]] = None
    ) -> List[Dict[str, Any]]:
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

    def update_data(self, table_name: str, item_id: Union[int, str], data: Dict[str, Any]):
        try:
            if isinstance(data, dict):
                set_values = ", ".join(f"{key} = ?" for key in data.keys())
                query = f"UPDATE {table_name} SET {set_values} WHERE id = ?"
                params = list(data.values()) + [item_id]
                self.execute_query(query, params)
            else:
                raise ValueError("Data must be a dictionary")
        except sqlite3.Error as e:
            print(f"Error updating data: {e}")
        except Exception as e:
            print(f"value error {e}")

    def drop_table(self, table_name: str) -> None:
        try:
            query = f"DROP TABLE IF EXISTS {table_name}"
            self.execute_query(query)
        except sqlite3.Error as e:
            print(f"Error dropping table: {e}")


if __name__ == "__main__":
    # Create an instance of the DatabaseHandler
    handler = DatabaseHandler("../../../spread.db")
    # Before creating the triggers, set the recursive_triggers pragma to ON
    handler.drop_table("spread")
    handler.drop_table("items")
    handler.drop_table("user")
    handler.drop_table("spread_user")

    """
    create tables
    """
    handler.create_table("spread",
                         ["id INTEGER PRIMARY KEY",
                          "name TEXT", "capital INTEGER",
                          "mtm INTEGER", "tp INTEGER",
                          "sl INTEGER", "max_mtm INTEGER",
                          "trail_after INTEGER",
                          "trail_at INTEGER", "status INTEGER",
                          "created_at DATETIME DEFAULT CURRENT_TIMESTAMP"])
    # Create the "items" table
    handler.create_table("items", ["id INTEGER PRIMARY KEY", "token TEXT",
                                   "spread_id INTEGER", "symbol TEXT",
                                   "exchange TEXT", "entry REAL",
                                   "side INTEGER", "quantity INTEGER",
                                   "mtm INTEGER", "ltp REAL"])
    handler.create_table("user",
                         ["id INTEGER PRIMARY KEY",
                          "broker_id TEXT",
                          "user TEXT"])
    handler.create_table("spread_user",
                         ["id INTEGER PRIMARY KEY",
                          "spread_id INTEGER",
                          "broker_id TEXT"])
    spread_data_1 = {
        "name": "First Spread",
        "capital": -176,
        "mtm": 0,
        "tp": 80,
        "sl": 50,
        "max_mtm": 0,
        "trail_after": 50,
        "trail_at": 40,
        "status": 1}
    spread_data_2 = {
        "name": "Second Spread 2",
        "capital": 100,
        "mtm": 0,
        "tp": 10,
        "sl": 5,
        "max_mtm": 0,
        "trail_after": 20,
        "trail_at": 15,
        "status": 1}
    handler.insert_data("spread", spread_data_1)
    handler.insert_data("spread", spread_data_2)
    """
    items_data_1 = {
        "spread_id": 1,
        "token": "73311",
        "symbol": "HINDALCO31AUG23440PE",
        "exchange": "NFO",
        "entry": 0.5,
        "side": -1,
        "quantity": 1,
        "mtm": 0.5,
        "ltp": 0.5
    }
    items_data_2 = {
        "spread_id": 1,
        "token": "73310",
        "symbol": "HINDALCO31AUG23445CE",
        "exchange": "NFO",
        "entry": 176,
        "side": -1,
        "quantity": 1,
        "mtm": 0,
        "ltp": 176
    }
    handler.insert_data("items", items_data_1)
    handler.insert_data("items", items_data_2)
    """
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
    updated_item_1 = {
        "exchange": "NFO",
        "token": "127900",
        "ltp": 120  # Updated ltp value
    }
    updated_item_2 = {
        "exchange": "NFO",
        "token": "127901",
        "ltp": 130  # Updated ltp value
    }
    # Update the row, excluding the 'mtm' field
    # query = """
    #   UPDATE items
    #   SET ltp = :ltp
    #   WHERE exchange = :exchange and token = :token
    #   """
    """
    handler.execute_query(query, updated_item_1)
    handler.execute_query(query, updated_item_2)
    """
    # Fetch the updated data from the "items" table
    query = "SELECT * FROM items"
    updated_items = handler.fetch_data(query, )

    query = """
        SELECT spread.*
        FROM spread
        where status >= 0
    """
    spreads = handler.fetch_data(query, )

    # Insert Users
    users_data = [
        {"broker_id": "A1079542", "user": "AnjuAgrawal"},
        {"broker_id": "K583959", "user": "KALPANAKATH"},
        {"broker_id": "PETT1665", "user": "MAHESHKAATH"},
        {"broker_id": "S1521310", "user": "SANDEEPAWAL"},
        {"broker_id": "DESV1032", "user": "HARSHITBONI"},
        {"broker_id": "P824460", "user": "Priyankarya"},
        {"broker_id": "PETT1707", "user": "SANDEEPAHUF"},
        {"broker_id": "R1001548", "user": "RaghavAgwal"},
        {"broker_id": "D537510", "user": "DoyalKayyal"},
    ]
    for user_data in users_data:
        query = "INSERT INTO user (broker_id, user) VALUES (?, ?)"
        params = (user_data["broker_id"], user_data["user"])
        handler.execute_query(query, params)

    # Create Spread User table
    handler.create_table("spread_user",
                         ["id INTEGER PRIMARY KEY",
                          "spread_id INTEGER",
                          "broker_id TEXT"])

    # Print the retrieved items
    for spread in spreads:
        print(spread)
    # Print the updated item
    for item in updated_items:
        print(item)
    # Disconnect from the database
    handler.disconnect()
