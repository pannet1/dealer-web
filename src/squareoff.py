from user import _random_broker
from wsocket import Wsocket


def get_cred():
    h = _random_broker()
    return dict(
        auth_token=h.access_token,
        api_key=h._api_key,
        client_code=h._user_id,
        feed_token=h.obj.feed_token,
    )


dct = get_cred()
old_tokens = {"exchangeType": 1, "tokens": ["26000"]}
t1 = Wsocket(dct, old_tokens)
t1.start()
print("started")

while not t1.is_open:
    print("waiting for wsocket ...")
    __import__("time").sleep(1)
else:
    print(f"ticks: {t1.ticks}")
    new_tokens = {"exchangeType": 2, "tokens": ["57920"]}
    t1.subscribe(new_tokens)

while t1.is_open:
    print(f"ticks: {t1.ticks}")
    __import__("time").sleep(1)
