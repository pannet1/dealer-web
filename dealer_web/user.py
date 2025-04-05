from api_helper import write_to_pickle
from constants import sec_dir, futil, XLS
from stock_brokers.angelone.angel_one import AngelOne
import pickle


def load_all_users():
    print("loading users")
    O_USERS = []
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
            O_USERS.append(a)
        else:
            print(f"unable to authenticate user {user['user_id']}")

    return O_USERS
