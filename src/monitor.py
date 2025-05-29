from constants import alerts_json, futil
from pprint import pprint
from user import get_ltps, load_all_users
from api_helper import get_tkn_fm_sym

class Monitor:
    def __init__(self):
        self.tokens = []
        # find names of trading symbols
        self.alerts: list= futil.read_file(alerts_json)["alerts"]
        self.users = load_all_users()
        self._find_token_from_symbol()

    def _find_token_from_symbol(self ):
        # find token and dummy ltp
        for alert in self.alerts:
            alert["instrument_token"] = get_tkn_fm_sym(sym=alert["name"], exch="NSE")
            alert["ltp"]  = 0
            self.tokens.append(alert["instrument_token"])
        pprint(self.alerts)

    def _update_equity_ltp(self):
        try:
            resp = get_ltps("NSE", self.tokens)
            for alert in self.alerts:
                # the value of mataches with value 
                if alert["instrument_token"] in resp:
                    alert["ltp"] = resp[alert["instrument_token"]]
        except Exception as e:
            print(e)

    def run(self):
        try:
            self._update_equity_ltp()
            actions = []
            for alert in self.alerts:
                if alert["ltp"] > float(alert["above"]) or alert["ltp"] < float(alert["below"]):
                    # send alert
                    print("send alert")
                    # add a new tradingsymbol key and value to actions
                    for action in alert["actions"]:
                        action["tradingsymbol"] = action["name"]
                    # add it to todo actions list
                    actions.append(alert["actions"])
                    # delete the added actions
                    alert.pop("actions")
                    __import__("time").sleep(1)

            pprint(actions)
        except Exception as e:
            print(e)


if __name__ == "__main__":
    try:
        monitor = Monitor()
        monitor.run()
        __import__("time").sleep(1)
    except KeyboardInterrupt as k:
        print("pressed ctrl c")
        __import__("sys").exit()
