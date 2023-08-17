from toolkit.fileutils import Fileutils
from omspy_brokers.angel_one import AngelOne
from requests import get
import json
import random
import pickle

futil = Fileutils()
sec_dir = "../../../"
dumpfile = sec_dir + "symbols.json"


class UserManager:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if not cls._initialized:
                cls._instance.initialize_users()
                cls._initialized = True
        return cls._instance

    def initialize_users(self):
        def write_to_pickle(pkl, ao_obj):
            print("writing to pickle file for user: " + ao_obj._user_id)
            dct = {
                "user_id": ao_obj._user_id,
                "api_key": ao_obj._api_key,
                "totp": ao_obj._totp,
                "password": ao_obj._password,
                "access_token": ao_obj.access_token,
                "refresh_token": ao_obj.refresh_token,
                "feed_token": ao_obj.feed_token,
                "client_name": ao_obj.client_name
            }
            with open(pkl, "wb") as f:
                pickle.dump(dct, f)

        self.ao = []
        users = futil.xls_to_dict(sec_dir + "ao_users.xls")
        for user in users:
            pklfile = sec_dir + user['user_id'] + ".pkl"
            flag = futil.is_file_not_2day(pklfile)
            if flag:
                a = AngelOne(user['user_id'], user['api_key'],
                             user['totp'], user['password'])
            else:
                print("loading from pickle file user: " + user['user_id'])
                with open(pklfile, "rb") as p:
                    pkld = pickle.load(p)
                a = AngelOne(pkld['user_id'], pkld['api_key'], pkld['totp'],
                             pkld['password'], pkld['access_token'], pkld['refresh_token'],
                             pkld['feed_token'])
            if a.authenticate():
                if flag:
                    print(f"writing to pickle file {pklfile}")
                    write_to_pickle(pklfile, a)
                a._userid = user['user_id']
                a._multiplier = user['multiplier']
                a._max_loss = user['max_loss']
                a._target = user['target']
                a._disabled = user['disabled']
                self.ao.append(a)
            else:
                print(f"unable to authenticate user {user['user_id']}")


# Use the UserManager to access the initialized ao list


def random_broker(ao=None) -> AngelOne:
    i = random.randint(0, len(ao) - 1)
    return ao[i]


def orders(args=None, ao=None):
    if ao is None:
        ao = user_manager.ao
    th, td, mh, md = [], [], [], []
    for a in ao:
        resp = a.orders
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if 'message' in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def trades(ao=None):
    th, td, mh, md = [], [], [], []
    for a in ao:
        resp = a.trades
        lst = resp_to_lst(resp)
        args = ['tradingsymbol', 'optiontype',
                'transactiontype', 'tradevalue', 'fillprice']
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if 'message' in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def positions(ao=None):
    if ao is None:
        ao = user_manager.ao
    th, td, mh, md = [], [], [], []
    for a in ao:
        resp = a.positions
        lst = resp_to_lst(resp)
        args = [
            'exchange', 'tradingsymbol', 'producttype', 'optiontype',
            'netqty', 'pnl', 'ltp', 'avgnetprice', 'netprice'
        ]
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if 'message' in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def margins(args=None, ao=None):
    if ao is None:
        ao = user_manager.ao
    th, td, mh, md = [], [], [], []
    for a in ao:
        resp = a.margins
        if resp.get('data') is not None:
            resp['data']['userid'] = a._userid
        lst = resp_to_lst(resp)
        if not args:
            args = ['userid', 'net', 'availablecash', 'm2munrealized', 'utiliseddebits',
                    'utilisedpayout']
        th1, td1 = lst_to_tbl(lst, args, client_name=a.client_name)
        if 'message' in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def order_place_by_user(client_name, kwargs):
    th, td, mh, md = [], [], [], []
    a = get_broker_by_id(client_name)
    resp = a.order_place(**kwargs)
    if resp:
        lst = resp_to_lst(resp)
        th1, td1 = lst_to_tbl(lst, client_name=a.client_name)
        if 'message' in th1:
            mh = th1
            md += td1
        else:
            th = th1
            td += td1
    return mh, md, th, td


def order_modify_by_user(client_name, kwargs):
    th, td, mh, md = [], [], [], []
    a = get_broker_by_id(client_name)
    resp = a.order_modify(kwargs)
    print(kwargs)
    print(resp)
    lst = resp_to_lst(resp)
    th1, td1 = lst_to_tbl(lst, client_name=a.client_name)
    if 'message' in th1:
        mh = th1
        md += td1
    else:
        th = th1
        td += td1
    return mh, md, th, td


def order_cancel(client_name, order_id, variety):
    th, td, mh, md = [], [], [], []
    a = get_broker_by_id(client_name)
    resp = a.order_cancel(order_id, variety)
    lst = resp_to_lst(resp)
    th1, td1 = lst_to_tbl(lst, client_name=a.client_name)
    if 'message' in th1:
        mh = th1
        md += td1
    else:
        th = th1
        td += td1
    return mh, md, th, td


# equity trade functions
#

def get_broker_by_id(client_name: str, ao=None) -> AngelOne:
    if ao is None:
        ao = user_manager.ao
    for a in ao:
        if a.client_name == client_name:
            return a


def lst_to_tbl(lst, args=None, kwargs=None, client_name: str = None):
    def filter_dict(dct, args=None, kwargs=None):
        new_dct = {}
        if args and len(args) > 0:
            for k, v in dct.items():
                if k in args:
                    new_dct[k] = v
            if any(new_dct):
                new_dct['client_name'] = client_name
                return new_dct
            else:
                dct['client_name'] = client_name
                return dct

        # not tested
        elif kwargs and len(kwargs) > 0:
            for d in dct:
                case = True
                for k, v in kwargs.items():
                    if d.get(k) != v:
                        case = False
                if case:
                    new_dct.append(d)
            return new_dct
        else:
            user_dct = {'client_name': client_name}
            for k, v in dct.items():
                user_dct[k] = v
            return user_dct

    new = []
    for dct in lst:
        f_dct = filter_dict(dct, args, kwargs)
        new.append(f_dct)

    th, body = ['message'], []
    for f_dct in new:
        k = f_dct.keys()
        th = list(k)
        v = f_dct.values()
        td = list(v)
        body.append(td)
    if len(body) > 0:
        return th, body
    body = ['not a dictionary']
    return th, body


def resp_to_lst(resp):
    if not resp:
        return [{
            'message': 'no response'
        }]

    elif 'data' in resp:
        if type(resp['data']) == list:
            return resp['data']
        elif resp['data'] is None:
            return [{'message': 'no data'}]
        else:
            return [resp['data']]

    if isinstance(resp, (str, int)):
        return [{'response': resp}]
    elif isinstance(resp, dict):
        return [resp]
    elif isinstance(resp, list):
        return resp

    message = (f"unexpected response of type: {type(resp)}")
    return [{
        'message': message
    }]


def get_ltp(exch, sym, tkn):
    ao = random_broker()
    resp = ao.obj.ltpData(exch, sym, tkn)
    lst = resp_to_lst(resp)
    head, ltp = lst_to_tbl(lst, ['ltp'], client_name=a.client_name)
    return head, ltp


def get_symbols(search):
    f = open(dumpfile)
    data = json.load(f)
    s_key = len(search)
    if s_key > 0:
        j = []
        for i in data:
            if i['symbol'][:s_key] == search.upper():
                # ltp = get_ltp(i['exch_seg'], i['symbol'], i['token'])
                # i['ltp'] = ltp[0]
                j.append(i)
                if len(j) > 15:
                    break
        f.close()
        args = ['exch_seg', 'symbol', 'token', 'lotsize']
        th, td = lst_to_tbl(j, args, client_name=a.client_name)
        return th, td


def get_token(row):
    try:
        f = open(dumpfile)
        data = json.load(f)
        length = len(row.symbol)
        print(row.symbol)
        if length > 0:
            for i in data:
                if i['symbol'][:length] == row.symbol.upper():
                    token = i['token']
            f.close()
            return token
    except Exception as e:
        print(e)
        return 0
    else:
        return token


def contracts():
    if futil.is_file_not_2day(dumpfile):
        headers = {
            "Host": "angelbroking.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        resp = get(url, headers=headers)
        with open(dumpfile, "w") as json_file:
            json_file.write(resp.text)
        json_file, resp = None, None


def get_tkn_fm_sym(sym):
    try:
        f = open(dumpfile)
        data = json.load(f)
        token = next((item.get("token")
                     for item in data if item.get("symbol") == sym), 0)
        f.close
        return token
    except Exception as e:
        print(f"{e} occured while get_tkn_fm_sym")


if __name__ == '__main__':
    sub_list = [
        {"symbol": 'PEL27JUL23920PE', "exch_seg": "NFO"},
        {"symbol": 'PEL27JUL23920CE', "exch_seg": "NFO"},
    ]
    sub_list_with_tokens = get_ws_symbols(sub_list)
    print(sub_list_with_tokens)
