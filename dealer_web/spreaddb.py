from toolkit.fileutils import Fileutils
from database_handler import DatabaseHandler
from copy import deepcopy
from typing import Dict, List, Any


class SpreadDB(DatabaseHandler):

    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self.mtime = ""
        self.qry_items = """
            SELECT items.id, items.token, items.symbol, items.exchange,
            items.side, items.spread_id, items.entry, items.quantity, items.ltp
            FROM items, spread
            WHERE spread.status >= 0
            AND spread.id = items.spread_id
        """
        self.qry_spread = """
            SELECT spread.*
            FROM spread
            WHERE spread.status >= 0
        """
        self.qry_symbols = """
            SELECT exchange, token
            FROM items, spread
            WHERE spread.status >= 0
            AND spread.id = items.spread_id
        """
        super().__init__(db_name)
        self.items_data = super().fetch_data(self.qry_items)
        self.spread_data = super().fetch_data(self.qry_spread)

    def get_file_mtime(self):
        return Fileutils().get_file_mtime(self.db_name)

    def set_file_mtime(self, mtime: str):
        print(f"overwriting {self.mtime} with {mtime}")
        self.mtime = mtime

    def get_items(self):
        return self.fetch_data(self.qry_items)

    def get_spread(self):
        return self.fetch_data(self.qry_spread)

    def set_items(self, items_data: List[Dict[str, Any]]):
        self.items_data = items_data

    def set_spread(self, spread_data: List[Dict[str, Any]]):
        self.spread_data = spread_data

    def symbol_keys(self):
        lst_exch_token = []
        unique_exch_tokens = set()
        for item in self.fetch_data(self.qry_symbols):
            exchange = item["exchange"]
            token = str(item["token"])
            unique_exch_tokens.add(f"{exchange}:{token}")
        lst_exch_token = list(unique_exch_tokens)
        return lst_exch_token

    def dump_memory(self, table: str, data: List[Dict[str, Any]], lst_pop_keys=[]):
        for dct in data:
            param = deepcopy(dct)
            for key in lst_pop_keys:
                param.pop(key)
            id = param.pop('id')
            self.update_data(table, id, param)
