from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading
import time
from typing import List, Dict, Any
from quantsap import db_changed, monitor
from spreaddb import SpreadDB


class WebsocketClient(threading.Thread):
    def __init__(self, kwargs):
        self.is_open = False
        self.exch_str_int = {'NSE': 1, 'NFO': 2,
                             'BSE': 3, 'MCX': 5, 'NCDEX': 7, 'CDS': 13}
        self.exch_int_str = {1: 'NSE',  2: 'NFO',
                             3: 'BSE',  5: 'MCX', 7: 'NCDEX', 13: 'CDS'}
        """
        self.token_list = [
            {
                "exchangeType": 1,
                "tokens": ["26000", "26009"],
            }
        ]
        """
        self.token_list = []
        self.ticks = {}
        self.auth_token = kwargs['auth_token'],
        self.api_key = kwargs['api_key'],
        self.client_code = kwargs['client_code'],
        self.feed_token = kwargs['feed_token']
        self.sws = SmartWebSocketV2(**kwargs)
        threading.Thread.__init__(self)

    def on_data(self, wsapp, msg):
        self.ticks = {self.exch_int_str[msg['exchange_type']] +
                      ":" + str(msg['token']): msg['last_traded_price'] / 100}

    def on_open(self, wsapp):
        print("on open")
        self.is_open = True

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

    def subscribe(self, lst_token: List[Dict[str, Any]], correlation_id="spread", mode=1):
        self.sws.subscribe(correlation_id, mode, lst_token)

    def unsubscribe(self, lst_token, correlation_id="spread", mode=1):
        self.sws.unsubscribe(correlation_id, mode, lst_token)


if __name__ == "__main__":
    import user

    def get_cred():
        h = user.get_broker_by_id("HARSHITBONI")
        if (
            h is not None
            and isinstance(h.sess, dict)
        ):
            sess = h.sess
            if (
                sess['data'] is not None and
                sess['data'].get('jwtToken', False) is not None
            ):
                dct = dict(
                    auth_token=h.sess['data']['jwtToken'].split(' ')[1],
                    api_key=h._api_key,
                    client_code=h._user_id,
                    feed_token=h.obj.feed_token
                )
                return dct

    handler = SpreadDB("../../../spread.db")
    dct = get_cred()
    print(dct)
    t1 = WebsocketClient(dct)
    t1.start()

    while len(t1.token_list) == 0:
        t1.token_list = handler.kv_for_subscribing(t1.exch_str_int)
        time.sleep(1)

    while True:
        print(f"ticks: {t1.ticks}")
        curr_time = handler._get_curr_time()
        last_time = handler.last_update_time.add(minutes=5)
        if curr_time > last_time:
            new_tokens = handler.kv_for_subscribing(t1.exch_str_int)
            if any(new_tokens):
                if any(t1.token_list) and t1.is_open:
                    print(f"unsubscribing: {t1.token_list}")
                    t1.unsubscribe(t1.token_list)
                if t1.is_open:
                    print(f"subscribing : {new_tokens} ")
                    t1.subscribe(new_tokens)
                    t1.token_list = new_tokens
            db_changed(handler)
            handler._set_update_time(last_time)
        else:
            print(f"{curr_time} > {last_time} {curr_time > last_time}")
            monitor(handler, t1.ticks)
        time.sleep(1)

    """
    token_list = [
        {
            "exchangeType": 1,
            "tokens": ["26022", "26023"]
        }
    ]
    """
