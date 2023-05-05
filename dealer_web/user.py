from toolkit.fileutils import Fileutils
from omspy_brokers.angel_one import AngelOne
from requests import get
import json
import random

futil = Fileutils()
users = futil.xls_to_dict("../../confid/ao_users.xls")
ao = []


for user in users:
    a = AngelOne(**user)
    if a.authenticate():
        ao.append(a)

dumpfile = "../../confid/symbols.json"


def random_broker() -> AngelOne:
    i = random.randint(0, len(ao) - 1)
    return ao[i]


def get_broker_by_id(client_name: str) -> AngelOne:
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

    if any(resp):
        # if 'message' in resp:
        #    return [resp]

        if 'data' in resp:
            if type(resp['data']) == list:
                return resp['data']
            elif type(resp['data']) == dict:
                return [resp['data']]
            elif resp['data'] is None:
                return [{
                    'message': 'no data'
                }]
    return [{
        'message': 'something unexpected happened'
    }]


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


def get_ltp(exch, sym, tkn):
    ao = random_broker()
    resp = ao.obj.ltpData(exch, sym, tkn)
    lst = resp_to_lst(resp)
    head, ltp = lst_to_tbl(lst, ['ltp'], client_name=a.client_name)
    return head, ltp


def get_symbols(search):
    f = open(dumpfile)
    data = json.load(f)
    l = len(search)
    if l > 0:
        j = []
        for i in data:
            if i['symbol'][:l] == search.upper():
                # ltp = get_ltp(i['exch_seg'], i['symbol'], i['token'])
                # i['ltp'] = ltp[0]
                j.append(i)
                if len(j) > 15:
                    break
        f.close()
        args = ['exch_seg', 'symbol', 'token', 'lotsize']
        th, td = lst_to_tbl(j, args, client_name=a.client_name)
        return th, td


def orders(args=None):
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


def trades():
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


def positions():
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


def margins(args=None):
    th, td, mh, md = [], [], [], []
    for a in ao:
        resp = a.margins
        lst = resp_to_lst(resp)
        if not args:
            args = ['net', 'availablecash', 'm2munrealized', 'utiliseddebits',
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
def get_users():
    return ao


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
