from constants import futil, dumpfile
from requests import get
import pickle
import json


def contracts():
    if futil.is_file_not_2day(dumpfile):
        headers = {
            "Host": "angelbroking.com",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        resp = get(url, headers=headers)
        with open(dumpfile, "w") as json_file:
            json_file.write(resp.text)
        json_file, resp = None, None


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
        "client_name": ao_obj.client_name,
    }
    with open(pkl, "wb") as f:
        pickle.dump(dct, f)


def _filter_dict(dct, args=None, kwargs=None, client_name=None):
    new_dct = {}
    if args and len(args) > 0:
        for k, v in dct.items():
            if k in args:
                new_dct[k] = v
        if any(new_dct):
            new_dct["client_name"] = client_name
            return new_dct
        else:
            dct["client_name"] = client_name
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
        user_dct = {"client_name": client_name}
        for k, v in dct.items():
            user_dct[k] = v
        return user_dct


def lst_to_tbl(lst, args=None, kwargs=None, client_name=None):
    new = []
    for dct in lst:
        f_dct = _filter_dict(dct, args, kwargs, client_name)
        new.append(f_dct)

    th, body = ["message"], []
    for f_dct in new:
        k = f_dct.keys()
        th = list(k)
        v = f_dct.values()
        td = list(v)
        body.append(td)
    if len(body) > 0:
        return th, body
    body = ["not a dictionary"]
    return th, body


def resp_to_lst(resp):
    if not resp:
        return [{"message": "no response"}]

    elif "data" in resp:
        if isinstance(resp["data"], list):
            return resp["data"]
        elif resp["data"] is None:
            return [{"message": "no data"}]
        else:
            return [resp["data"]]

    if isinstance(resp, (str, int)):
        return [{"response": resp}]
    elif isinstance(resp, dict):
        return [resp]
    elif isinstance(resp, list):
        return resp

    message = f"unexpected response of type: {type(resp)}"
    return [{"message": message}]


def get_symbols(search):
    f = open(dumpfile)
    data = json.load(f)
    s_key = len(search)
    if s_key > 0:
        j = []
        for i in data:
            if i["symbol"][:s_key] == search.upper():
                # ltp = get_ltp(i['exch_seg'], i['symbol'], i['token'])
                # i['ltp'] = ltp[0]
                j.append(i)
                if len(j) > 15:
                    break
        f.close()
        args = ["exch_seg", "symbol", "token", "lotsize"]
        th, td = lst_to_tbl(j, args)
        return th, td


def get_tkn_fm_sym(sym, exch):
    """
    consumed by close_position in main
    """
    token = "0"
    with open(dumpfile, "r") as objfile:
        data = json.load(objfile)
        for i in data:
            if i["symbol"] == sym:
                print("sym match")
                print(i)
                print(f"{sym=}{exch=}")
            if (i["symbol"] == sym) and (i["exch_seg"] == exch):
                return i["token"]
    return token


def get_token(row):
    """
    marked for removal
    """
    try:
        token = 0
        f = open(dumpfile)
        data = json.load(f)
        length = len(row.symbol)
        print(row.symbol)
        if length > 0:
            for i in data:
                if i["symbol"][:length] == row.symbol.upper():
                    token = i["token"]
                    break
            f.close()
    except Exception as e:
        print(e)
    finally:
        return token
