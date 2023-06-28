from api_helper import ShoonyaApiPy
import time
import yaml
import pandas as pd

import time


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        original_return_val = func(*args, **kwargs)
        end = time.perf_counter()
        print("time elapsed in ", func.__name__, ": ", end - start, sep="")
        return original_return_val

    return wrapper


with open("cred.yml") as f:
    cred = yaml.load(f, Loader=yaml.FullLoader)
    print(cred)

import pyotp

otp = pyotp.TOTP(cred["secret"])
totp = otp.now()
# start of our program
api = ShoonyaApiPy()

ret = api.login(
    userid=cred["user"],
    password=cred["pwd"],
    twoFA=totp,
    vendor_code=cred["vc"],
    api_secret=cred["apikey"],
    imei=cred["imei"],
)


@timing_decorator
def option_chain_example():
    data = api.get_option_chain("NFO", "NIFTY12JAN23P18000", "18000", count=30)
    print(data)
    df = pd.DataFrame(data["values"])
    print(df)
    print(df.tsym.values)


if ret != None:
    alert_id = api.place_gtt_order(
        "SBIN-EQ",
        "NSE",
        api.ALERT_TYPE_BELOW,
        573.4,
        "S",
        "I",
        5,
        "LMT",
        575.3,
        "checking gtt below",
    )
    print("===================================")
    print(f"Alert ID for GTT Order :: {alert_id}")
    print("===================================")

    resp = api.get_pending_gtt_orders()
    print(resp)
    print(resp[0]['al_id'])
    print("===================================")

    alert_id = api.place_gtt_oco_mkt_order(
        "SILVERMIC28FEB23",
        "MCX",
        69200.0,
        69000.0,
        api.TRANSACTION_TYPE_SELL,
        api.PRODUCT_TYPE_INTRADAY,
        1,
    )
    print("===================================")

    print("===================================")
    print(f"Alert ID for GTT OCO MKT Order :: {alert_id}")
    print("===================================")
    time.sleep(1.0)
    resp = api.get_pending_gtt_orders()
    print("===================================")
    print("Pending GTT orders\n", resp)
    print("===================================")

    print("===================================")

    alert_id = api.modify_gtt_oco_mkt_order(
        "SILVERMIC28FEB23",
        "MCX",
        alert_id,
        69500.0,
        69100.0,
        api.TRANSACTION_TYPE_SELL,
        api.PRODUCT_TYPE_INTRADAY,
        1
    )

    print("===================================")
    print(f"Alert ID for Modified GTT OCO MKT Order :: {alert_id}")
    print("===================================")

    time.sleep(1.0)
    resp = api.get_pending_gtt_orders()
    print("===================================")
    print("Pending GTT orders\n", resp)
    print("===================================")

    for i in range(0, len(resp)):
        print(
            f'Cancelled GTT Order/Alert - Alert Id :: {api.cancelgtt(resp[i]["al_id"])}'
        )

    print("===================================")
    time.sleep(1.0)
    resp = api.get_pending_gtt_orders()
    print("===================================")
    print(resp)

    api.logout()
