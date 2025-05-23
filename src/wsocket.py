from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading
from typing import List, Dict, Any


class Wsocket(threading.Thread):
    """
    self.token_list = [
        {
            "exchangeType": 1,
            "tokens": ["26000", "26009"],
        }
    ]
    """

    exch_str_int = {"NSE": 1, "NFO": 2, "BSE": 3, "MCX": 5, "NCDEX": 7, "CDS": 13}
    exch_int_str = {1: "NSE", 2: "NFO", 3: "BSE", 5: "MCX", 7: "NCDEX", 13: "CDS"}
    ticks = {}
    token_list = []

    def __init__(self, kwargs, token):
        self.token = token
        self.is_open = False
        self.auth_token = kwargs["auth_token"]
        self.api_key = kwargs["api_key"]
        self.client_code = kwargs["client_code"]
        self.feed_token = kwargs["feed_token"]
        self.sws = SmartWebSocketV2(
            auth_token=self.auth_token,
            api_key=self.api_key,
            client_code=self.client_code,
            feed_token=self.feed_token,
        )
        threading.Thread.__init__(self)

    def on_data(self, wsapp, msg):
        print(msg)
        new_tick = {
            self.exch_int_str[msg["exchange_type"]]
            + ":"
            + msg["token"]: msg["last_traded_price"] / 100
        }
        self.ticks.update(new_tick)

    def on_open(self, wsapp):
        print("on open")
        self.is_open = True
        self.subscribe(self.token)

    def on_error(self, wsapp, error):
        print(error)

    def on_close(self, wsapp):
        self.is_open = False
        print("Close")

    def run(self):
        # Assign the callbacks.
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close
        self.sws.connect()

    def close_connection(self):
        self.sws.close_connection()

    def subscribe(self, token: Dict[str, Any]):
        self.token_list.append(token)
        print(self.token_list)
        self.sws.subscribe(correlation_id="spread", mode=1, token_list=self.token_list)

    def unsubscribe(self, lst_token, correlation_id="spread", mode=1):
        self.sws.unsubscribe(correlation_id, mode, lst_token)
