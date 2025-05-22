from toolkit.fileutils import Fileutils
from sqlite.database_handler import DatabaseHandler
from copy import deepcopy
from typing import Dict, List, Any
import pendulum


class SpreadDB(DatabaseHandler):

    def __init__(self, db_name: str) -> None:
        self.db_name = db_name
        self.last_update_time = self._get_curr_time().subtract(minutes=60)
        self.qry_items = """
        SELECT items.id, items.token, items.symbol, items.exchange,
        items.side, items.spread_id, items.entry, items.quantity, items.ltp
        FROM items
        WHERE items.spread_id IN (
            SELECT spread.id
            FROM spread
            WHERE spread.status >= 0
        )
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

    def _get_file_mtime(self):
        mtime = Fileutils().get_file_mtime(self.db_name)
        return pendulum.from_format(mtime, 'YYYY-MM-DD HH:mm:ss')

    def _set_update_time(self, ctime=None):
        self.last_update_time = ctime if ctime else self._get_curr_time()

    def _get_curr_time(self):
        return pendulum.now('UTC').add(hours=5, minutes=30)

    def get_users(self, spread_id: int):
        qry_users = """
            SELECT user.user
            FROM spread, user, spread_user
            WHERE spread_user.broker_id = user.broker_id
            AND spread.id =:spread_id
        """
        return self.fetch_data(qry_users, {"spread_id": spread_id})

    def get_items(self):
        return self.fetch_data(self.qry_items)

    def get_spread(self):
        return self.fetch_data(self.qry_spread)

    def set_items(self, items_data: List[Dict[str, Any]]):
        self.items_data = items_data

    def set_spread(self, spread_data: List[Dict[str, Any]]):
        self.spread_data = spread_data

    def dump_memory(self, table: str,
                    data: List[Dict[str, Any]],
                    lst_pop_keys=[]):
        try:
            for dct in data:
                param = deepcopy(dct)
                for key in lst_pop_keys:
                    param.pop(key)
                id = param.pop('id')
                self.update_data(table, id, param)
        except Exception as e:
            print(f" dump memory {e}")

    def symbol_keys(self):
        """
        return: List of symbols, used for testing purpose only
        """
        lst_exch_token = []
        unique_exch_tokens = set()
        for item in self.fetch_data(self.qry_symbols):
            exchange = item["exchange"]
            token = str(item["token"])
            unique_exch_tokens.add(f"{exchange}:{token}")
        lst_exch_token = list(unique_exch_tokens)
        return lst_exch_token

    def kv_for_subscribing(self, exch_str_int):
        token_list = []
        temp_dict = {}
        for item in self.fetch_data(self.qry_symbols):
            exchange = item['exchange']
            token = item['token']
            if exchange in temp_dict:
                temp_dict[exchange].add(token)
            else:
                temp_dict[exchange] = {token}

        for exchange, tokens in temp_dict.items():
            token_list.append(
                {"exchangeType": exch_str_int[exchange], "tokens": list(tokens)})
        return token_list


if __name__ == "__main__":
    exch_str_int = {'NSE': 1, 'NFO': 2, 'BSE': 3,
                    'MCX': 5, 'NCDEX': 7, 'CDS': 13}
    handler = SpreadDB("../../spread.db")
    val = handler.kv_for_subscribing(exch_str_int)
