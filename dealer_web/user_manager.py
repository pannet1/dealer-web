from toolkit.fileutils import Fileutils
from omspy_brokers.angel_one import AngelOne
import pickle
from typing import List

futil = Fileutils()
sec_dir = "../../../"


def load_all_users():
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

    ao = []
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
            user['broker'] = a
            user['_user_id'] = a._user_id
            ao.append(user)
        else:
            print(f"unable to authenticate user {user['user_id']}")
    return ao


class UserManager:
    ao: List[AngelOne]

    def __init__(self):
        print("........... Init ............")
        cls = self.__class__
        cls.ao = load_all_users()
        print("......... class loaded .......... ")

    @classmethod
    def get_users(cls):
        print(".... CLASS METHOD .....")
        return cls.ao
