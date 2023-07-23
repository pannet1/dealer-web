import random
from toolkit.utilities import Utilities
from database_handler import DatabaseHandler
from pprint import pprint
import pandas as pd

# Create an instance of the DatabaseHandler
handler = DatabaseHandler("spread.db")


def yield_random_price() -> float:
    return random.uniform(10, 300)


while True:
    updated_item_1 = {
        "instrument": "ACC27JUL231840CE",
        "ltp": yield_random_price()  # Updated ltp value
    }
    updated_item_2 = {
        "instrument": "PEL27JUL23920PE",
        "ltp": yield_random_price()  # Updated ltp value
    }
    query = """
        SELECT items.instrument, items.exchange
        FROM items, spread
        where spread.status >= 0
        and spread.id = items.spread_id
    """
    instruments = handler.fetch_data(query, )
    pprint(instruments)
    Utilities().slp_for(2)
