from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from quantsap import db_changed, monitor
from spreaddb import SpreadDB


class WebsocketClient():
    def __init__(self, kwargs):
        self.is_open = False
        self.exch_str_int = {'NSE': 1, 'NFO': 2,
                             'BSE': 3, 'MCX': 5, 'NCDEX': 7, 'CDS': 13}
        self.exch_int_str = {1: 'NSE',  2: 'NFO',
                             3: 'BSE',  5: 'MCX', 7: 'NCDEX', 13: 'CDS'}
        self.ticks = []
        self.handler = SpreadDB("../../../spread.db")
        self.token_list = []
        self.auth_token = kwargs['auth_token'],
        self.api_key = kwargs['api_key'],
        self.client_code = kwargs['client_code'],
        self.feed_token = kwargs['feed_token']
        self.sws = SmartWebSocketV2(**kwargs)

    def on_data(self, wsapp, msg):
        ticks = {self.exch_int_str[msg['exchange_type']] +
                 ":" + str(msg['token']): msg['last_traded_price'] / 100}
        newtime = self.handler.get_file_mtime()
        print(f" {ticks} incoming ticks")
        if newtime != self.handler.mtime:
            if any(self.token_list):
                print(f"self tokens: {self.token_list} not empty")
                self.unsubscribe(self.token_list)
            new_tokens = self.handler.kv_for_subscribing(self.exch_str_int)
            if any(new_tokens):
                print(f" {new_tokens} subscribing new tokens")
                self.subscribe(new_tokens)
                self.token_list = new_tokens
            db_changed(self.handler, newtime)
        else:
            print("monitor")
            monitor(self.handler, ticks)

    def on_open(self, wsapp):
        print("on open")
        lst = {
            "exchangeType": 1,
            "tokens": ["26011", "26012"]
        },
        self.subscribe(lst, correlation_id="as", mode=1)

    def on_error(self, wsapp, error):
        print(error)

    def on_close(self, wsapp):
        self.is_open = False
        print("on close")

    def run(self):
        # Assign the callbacks.
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close
        self.sws.connect()

    def close_connection(self):
        self.sws.close_connection()

    def subscribe(self, lst_token, correlation_id="spread", mode=1):
        self.sws.subscribe(correlation_id, mode, lst_token)

    def unsubscribe(self, lst_token, correlation_id="spread", mode=1):
        self.sws.unsubscribe(correlation_id, mode, lst_token)


if __name__ == "__main__":
    import user

    def get_cred():
        print(user)
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

    dct = get_cred()
    t1 = WebsocketClient(dct)
    t1.run()
    """
    token_list = [
        {
            "exchangeType": 2,
            "tokens": ["73310", "73311"]
        }
    ]
    token_list = [
        {
            "exchangeType": 1,
            "tokens": ["26011"]
        }
    ]
    while t1.ticks == {}:
        print("sleeping")
        time.sleep(1)
    while True:
        print(t1.ticks)
        t1.subscribe("subs1", 1, token_list)
    """
