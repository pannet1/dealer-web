from api_helper import write_to_pickle
from constants import sec_dir, futil, XLS
from stock_brokers.angelone.angel_one import AngelOne
import pickle

import random
from api_helper import resp_to_lst, lst_to_tbl

_USERS = None


def load_all_users():
    print("loading users")
    global _USERS
    if _USERS is None:
        _USERS = []
        users = futil.xls_to_dict(XLS)
        for user in users:
            pklfile = sec_dir + user["user_id"] + ".pkl"
            flag = futil.is_file_not_2day(pklfile)
            if flag:
                a = AngelOne(
                    user["user_id"], user["api_key"], user["totp"], user["password"]
                )
            else:
                print("loading from pickle file user: " + user["user_id"])
                with open(pklfile, "rb") as p:
                    pkld = pickle.load(p)
                a = AngelOne(
                    pkld["user_id"],
                    pkld["api_key"],
                    pkld["totp"],
                    pkld["password"],
                    pkld["access_token"],
                    pkld["refresh_token"],
                    pkld["feed_token"],
                )
            if a.authenticate():
                if flag:
                    print(f"writing to pickle file {pklfile}")
                    write_to_pickle(pklfile, a)
                a._userid = user["user_id"]
                a._multiplier = user["multiplier"]
                a._max_loss = user["max_loss"]
                a._target = user["target"]
                a._disabled = user["disabled"]
                _USERS.append(a)
            else:
                print(f"unable to authenticate user {user['user_id']}")
    return _USERS


def get_broker_by_id(client_name: str):
    for a in load_all_users():
        if a.client_name == client_name:
            return a


def _random_broker():
    i = random.randint(0, len(load_all_users()) - 1)
    return load_all_users()[i]


def gtt(status=["FORALL"]):
    th, td, mh, md = [], [], [], []
    for a in load_all_users():
        resp = a.obj.gttLists(status=status, page=1, count=100)
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, args=None, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def orders(args=None):
    th, td, mh, md = [], [], [], []
    for a in load_all_users():
        resp = a.orders
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def trades():
    th, td, mh, md = [], [], [], []
    for a in load_all_users():
        resp = a.trades
        lst = resp_to_lst(resp)
        args = [
            "tradingsymbol",
            "optiontype",
            "transactiontype",
            "tradevalue",
            "fillprice",
        ]
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def positions():
    th, td, mh, md = [], [], [], []
    for a in load_all_users():
        resp = a.positions
        lst = resp_to_lst(resp)
        args = [
            "exchange",
            "tradingsymbol",
            "producttype",
            "optiontype",
            "netqty",
            "pnl",
            "ltp",
            "avgnetprice",
            "netprice",
        ]
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def margins(args=None):
    th, td, mh, md = [], [], [], []
    for a in load_all_users():
        resp = a.margins
        if resp.get("data") is not None:
            resp["data"]["userid"] = a._userid
        lst = resp_to_lst(resp)
        if not args:
            args = [
                "userid",
                "net",
                "availablecash",
                "m2munrealized",
                "utiliseddebits",
                "utilisedpayout",
            ]
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if "message" in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td

def get_ltps(params: dict) -> dict:
    try:
        new_dct = {}
        exch, lst_of_tokens = exch_token(params)

        # Batch the tokens into chunks of 50
        batch_size = 50
        for i in range(0, len(lst_of_tokens), batch_size):
            timer(1)
            token_batch: list = lst_of_tokens[i : i + batch_size]
            exch_token_dict = {exch: token_batch}

            # Fetch LTP for the current batch
            resp = Helper.api.obj.getMarketData("LTP", exch_token_dict)
            lst_of_dict = resp["data"]["fetched"]

            if isinstance(lst_of_dict, list):
                # Update the dictionary with the current batch's LTPs
                new_dct.update({dct["symbolToken"]: dct["ltp"] for dct in lst_of_dict})
    except Exception as e:
        print(f"Error while getting LTP: {e}")
    finally:
        return new_dct
        
def get_ltp(exch, sym, tkn):
    brkr = _random_broker()
    print(exch, sym, tkn)
    resp = brkr.obj.ltpData(exch, sym, tkn)
    print(f"{resp:}")
    lst = resp_to_lst(resp)
    print(f"{lst}")
    head, ltp = lst_to_tbl(lst, ["ltp"], client_name=brkr.client_name)
    print(f"{ltp}")
    return head, ltp
