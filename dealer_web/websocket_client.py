from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import threading


class WebsocketClient(threading.Thread):
    def __init__(self, kwargs):
        self.ticks = {}
        self.correlation_id = "abc123"
        self.action = 1
        self.mode = 1
        self.auth_token = kwargs['auth_token'],
        self.api_key = kwargs['api_key'],
        self.client_code = kwargs['client_code'],
        self.feed_token = kwargs['feed_token']
        self.sws = SmartWebSocketV2(**kwargs)
        threading.Thread.__init__(self)

    def on_data(self, wsapp, message):
        self.ticks = message
        # close_connection()

    def on_open(self, wsapp):
        print("on open")
        token_list = [
            {
                "exchangeType": 1,
                "tokens": ["26009"]
            }
        ]
        self.sws.subscribe(self.correlation_id, self.mode, token_list)
        # self.sws.unsubscribe(self.correlation_id, self.mode, self.token_list1)

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


if __name__ == "__main__":
    import user
    import time

    def get_cred():
        h = user.get_broker_by_id("HARSHITBONI")
        dct = dict(
            auth_token=h.sess['data']['jwtToken'].split(' ')[1],
            api_key=h._api_key,
            client_code=h._user_id,
            feed_token=h.obj.feed_token
        )
        return dct
    dct = get_cred()
    t1 = WebsocketClient(dct)
    t1.start()

    while True:
        token_list = [
            {
                "exchangeType": 1,
                "tokens": ["26011"]
            }
        ]
        print(t1.ticks)
        time.sleep(10)
