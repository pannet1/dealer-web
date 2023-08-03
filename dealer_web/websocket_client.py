from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading
import time


class WebsocketClient(threading.Thread):
    def __init__(self, kwargs, lst_tkn):
        self.is_open = False
        self.exch_str_int = {'NSE': 1, 'NFO': 2,
                             'BSE': 3, 'MCX': 5, 'NCDEX': 7, 'CDS': 13}
        self.exch_int_str = {1: 'NSE',  2: 'NFO',
                             3: 'BSE',  5: 'MCX', 7: 'NCDEX', 13: 'CDS'}
        self.ticks = {}
        self.token_list = lst_tkn
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
        token_list = [
            {
                "exchangeType": 1,
                "tokens": ["26011"]
            }
        ]
        self.subscribe(token_list, "subs1", 1)

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

    def subscribe(self, lst_token, correlation_id, mode):
        print("subscribe")
        self.sws.subscribe(correlation_id, mode, lst_token)

    def unsubscribe(self, lst_token, correlation_id, mode):
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

    dct = get_cred()
    print(dct)
    token_list = [
        {
            "exchangeType": 1,
            "tokens": ["26008"]
        }
    ]
    t1 = WebsocketClient(dct, token_list)
    t1.start()
    token_list = [
        {
            "exchangeType": 1,
            "tokens": ["26022", "26023"]
        }
    ]
    while t1.ticks == {}:
        time.sleep(1)
    while True:
        print(t1.ticks)
        t1.subscribe("subs1", 1, token_list)
