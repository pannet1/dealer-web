from constants import alerts_json, futil
from pprint import pprint
from user import get_ltps, load_all_users, positions, _random_broker
from api_helper import get_tkn_fm_sym
import pandas as pd
from wsocket import Wsocket



class Monitor:
    def __init__(self):
        # find names of trading symbols
        self.alerts: list= futil.read_file(alerts_json)["alerts"]
        self.users = load_all_users()
        self.tokens = self._tkn_fm_alert()
        df = self._tkn_fm_positions()
        if df is not None:
            self.symbol_token = df.dropna(subset=["token"]).set_index("tradingsymbol")["token"].to_dict()
            token_list = {
                    "exchangeType": 2,
                    "tokens": list(self.symbol_token.values())
                }
            h = _random_broker()
            kwargs = dict(
                auth_token=h.access_token,
                api_key=h._api_key,
                client_code=h._user_id,
                feed_token=h.obj.feed_token,
            )
            self.ws = Wsocket(kwargs=kwargs, token=token_list)
            self.ws.run()
        

    def _tkn_fm_positions(self):
        symbol_token = {}
        _, _, columns, data = positions()
        if not any(data):
            return None

        df = pd.DataFrame(data=data, columns=columns)
        df["token"] = None
        df["netqty"] = df["netqty"].astype(int)

        # condtions
        mask = (df["exchange"] == "NFO") & (df["netqty"] < 0 )
        df.loc[mask, "token"] = df.loc[mask].apply(
            lambda row: get_tkn_fm_sym(row["tradingsymbol"], "NFO"),
            axis=1
        )
        return df
        

    def _tkn_fm_alert(self ):
        # find token and dummy ltp
        tokens = []
        for alert in self.alerts:
            alert["instrument_token"] = get_tkn_fm_sym(sym=alert["name"], exch="NSE")
            alert["ltp"]  = 0
            tokens.append(alert["instrument_token"])
        return tokens 

    def _update_equity_ltp(self):
        try:
            resp = get_ltps("NSE", self.tokens)
            for alert in self.alerts:
                # the value of mataches with value 
                if alert["instrument_token"] in resp:
                    alert["ltp"] = resp[alert["instrument_token"]]
        except Exception as e:
            print(e)

    def _process_alert_actions(self, alert, event_type):
        # send alert
        print(f"ltp is {event_type} for {alert['name']}")
        actions = []
        for action in alert["actions"][:]:  # work on a shallow copy to avoid iteration issues
            if action["event"] == event_type:
                action["tradingsymbol"] = alert["name"]
                actions.append(action)
                alert["actions"].remove(action)  # safely remove from original list
        return actions


    def run(self):
        try:
            self._update_equity_ltp()
            pprint(self.alerts)
            actions = []
            for alert in self.alerts:
                if alert["ltp"] > float(alert["above"]):
                    actions += self._process_alert_actions(alert, "above")
                    __import__("time").sleep(1)
                elif alert["ltp"] < float(alert["below"]):
                    # send alert
                    actions += self._process_alert_actions(alert, "below")
                    __import__("time").sleep(1)
            pprint(actions)
            pprint(self.ws.ticks)
                
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
