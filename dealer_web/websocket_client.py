from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading


class WebsocketClient(threading.Thread):
    def __init__(self, kwargs, lst_tkn):
        self.ticks = {}
        self.token_list = lst_tkn
        self.auth_token = kwargs['auth_token'],
        self.api_key = kwargs['api_key'],
        self.client_code = kwargs['client_code'],
        self.feed_token = kwargs['feed_token']
        self.sws = SmartWebSocketV2(**kwargs)
        threading.Thread.__init__(self)

    def on_data(self, wsapp, msg):
        self.ticks[int(msg.get('token'))] = msg.get(
            'last_traded_price') / 100

    def on_open(self, wsapp):
        print("on open")
        self.subscribe("subs1", 1, self.token_list)

    def on_error(self, wsapp, error):
        print(error)

    def on_close(self, wsapp):
        print("Close")

    def close_connection(self):
        self.sws.close_connection()

    def run(self):
        # Assign the callbacks.
        self.sws.on_open = self.on_open
        self.sws.on_data = self.on_data
        self.sws.on_error = self.on_error
        self.sws.on_close = self.on_close
        self.sws.connect()

    def subscribe(self, correlation_id, mode, lst_token):
        print("subscribe")
        self.sws.subscribe(correlation_id, mode, lst_token)

    def unsubscribe(self, correlation_id, mode, lst_token):
        # self.sws.unsubscribe(correlation_id, mode, self.token_list)
        pass


if __name__ == "__main__":
    import user

    def get_cred():
        print(user)
        h = user.get_broker_by_id("HARSHITBONI")
        if (
            h is not None and
            h.sess is not None and
            h.sess.get['data'] is not None and
            h.sess['data'].get('jwtToken') is not None and
            h.sess['data'].get('jwtToken').split(' ')[1] is not None
        ):

            dct = dict(
                auth_token=h.sess['data']['jwtToken'].split(' ')[1],
                api_key=h._api_key,
                client_code=h._user_id,
                feed_token=h.obj.feed_token
            )
        return dct
    dct = get_cred()
    token_list = [
        {
            "exchangeType": 1,
            "tokens": ["26011"]
        }
    ]
    t1 = WebsocketClient(dct, token_list)
    t1.start()

    while True:
        print(t1.ticks)
