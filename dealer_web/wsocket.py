from SmartApi.smartWebSocketV2 import SmartWebSocketV2
import user

correlation_id = "abc123"
action = 1
mode = 1


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

token_list = [
    {
        "exchangeType": 1,
        "tokens": ["26009"]
    }
]
token_list1 = [
    {
        "action": 0,
        "exchangeType": 1,
        "tokens": ["26009"]
    }
]

sws = SmartWebSocketV2(**dct)


def on_data(wsapp, message):
    print("Ticks: {}".format(message))
    # close_connection()


def on_open(wsapp):
    print("on open")
    sws.subscribe(correlation_id, mode, token_list)
    # sws.unsubscribe(correlation_id, mode, token_list1)


def on_error(wsapp, error):
    print(error)


def on_close(wsapp):
    print("Close")


def close_connection():
    sws.close_connection()


# Assign the callbacks.
sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error
sws.on_close = on_close

sws.connect()
