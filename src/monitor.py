from constants import alerts_json, futil
from pprint import pprint
from user import get_ltps, load_all_users, positions, _random_broker, get_broker_by_id
from user_helper import _order_place_by_user
from api_helper import get_tkn_fm_sym
import pandas as pd
from wsocket import Wsocket
from copy import deepcopy
from traceback import print_exc
from logzero import logger as logging

def convert_price(price: int):
    price = price / 100
    price = round(price / 0.05) * 0.05
    return str(price)

class Monitor:

    def _df_fm_positions(self):
        symbol_token = {}
        _, _, columns, data = positions()
        if not any(data):
            return None
        df = pd.DataFrame(data=data, columns=columns)
        df["token"] = None
        df["netqty"] = df["netqty"].astype(int)
        mask = (df["exchange"] == "NFO") & (df["netqty"] < 0)
        df.loc[mask, "token"] = df.loc[mask].apply(
            lambda row: get_tkn_fm_sym(row["tradingsymbol"], "NFO"), axis=1
        )
        return df

    def _tkn_fm_alert(self):
        tokens = []
        for alert in self.alerts:
            alert["instrument_token"] = get_tkn_fm_sym(sym=alert["name"], exch="NSE")
            alert["ltp"] = 0
            tokens.append(alert["instrument_token"])
        return tokens

    def _flatten_askbid(self):
        try:
            flattened_ticks = []
            ticks = self.ws.ticks
            copied_ticks = deepcopy(ticks)
            for token, v in copied_ticks.items():
                dct = dict(
                    tradingsymbol=self.symbol_token[token],
                    ask=min(item["price"] for item in v["best_5_buy_data"]),
                    bid=max(item["price"] for item in v["best_5_sell_data"]),
                )
                flattened_ticks.append(dct)
            for ticks in flattened_ticks:
                ask, bid = ticks["ask"], ticks["bid"]
                if ask == 0 or bid == 0:
                    logging.warning(f'no tick for {ticks["tradingsymbol"]}')
                    continue
                ticks["is_trade"] = True if ((bid - ask) / ask * 100) < 20 else False
        except Exception as e:
            logging.error(f"{e} flatten askbid")
            print_exc()
        finally:
            return flattened_ticks

    def _split(self, tradingsymbol_to_be_split):
        if tradingsymbol_to_be_split.endswith("-EQ"):
            return tradingsymbol_to_be_split[:-3]
        elif tradingsymbol_to_be_split.endswith(" 50"):
            return tradingsymbol_to_be_split[:-3]
        else:
            return "STRING_IS_NOT_FOUND"

    def merge_ticks_df(self):
        try:
            merged_df = None
            df = self._df_fm_positions()
            # subscribe to new tokens
            if df is not None:
                symbol_token = (
                    df.dropna(subset=["token"])
                    .set_index("token")["tradingsymbol"]
                    .to_dict()
                )
                token_list = {"exchangeType": 2, "tokens": list(symbol_token.values())}
                self.symbol_token.update(symbol_token)

                flattened_ticks = self._flatten_askbid()
                if not any(flattened_ticks):
                    return

                flattened_df = pd.DataFrame(flattened_ticks)
                print(flattened_ticks)
                merged_df = pd.merge(df, flattened_df, on="tradingsymbol", how="inner")
        except Exception as e:
            print(f"{e} while cover")
        finally:
            return merged_df

    def cover_positions(self, row):
        params = {
            "tradingsymbol": row["tradingsymbol"],
            "symboltoken": row["token"],
            "transactiontype": "BUY",
            "exchange": row["exchange"],
            "price": convert_price(row["bid"]),
            "triggerprice": "0",

            "quantity": str(abs(row["netqty"])),
            "ordertype": "LIMIT",
            "producttype": row["producttype"],
            "variety": "NORMAL",
            "duration": "DAY",
        }
        client = row["client_name"]
        return _order_place_by_user(get_broker_by_id(client), params)

    def match_df_with_actions(self, df, actions):
        try:
            matching_df = None
            for action_item in actions:
                prefix = self._split(action_item["tradingsymbol"])
                matching_df = df[
                    df["tradingsymbol"].str.startswith(prefix)
                    & df["tradingsymbol"].str.contains(action_item["action"])
                    & (df["is_trade"] == True)
                ]
                if not matching_df.empty:
                    print(matching_df)
                    matching_df.apply(self.cover_positions, axis=1)

        except Exception as e:
            logging.error(f"{e} in match df with actions")
            print_exc()

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
        print(f"ltp is {event_type} for {alert['name']}")
        actions = []
        for action in alert["actions"][
            :
        ]:  # work on a shallow copy to avoid iteration issues
            if action["event"] == event_type:
                action["tradingsymbol"] = alert["name"]
                actions.append(action)
                alert["actions"].remove(action)  # safely remove from original list
        return actions

    def main(self):
        try:
            self._update_equity_ltp()
            pprint(self.alerts)
            actions = []
            for alert in self.alerts:
                if alert["ltp"] > float(alert["above"]):
                    actions += self._process_alert_actions(alert, "above")
                elif alert["ltp"] < float(alert["below"]):
                    actions += self._process_alert_actions(alert, "below")

            if any(actions):
                df = self.merge_ticks_df()
                if df is not None and not df.empty:
                    self.match_df_with_actions(df, actions)

            __import__("time").sleep(1)
        except Exception as e:
            print(e)
            print_exc()

    def __init__(self):
        self.alerts: list = futil.read_file(alerts_json)["alerts"]
        self.users = load_all_users()
        self.tokens = self._tkn_fm_alert()
        df = self._df_fm_positions()
        if df is not None:
            self.symbol_token = (
                df.dropna(subset=["token"])
                .set_index("token")["tradingsymbol"]
                .to_dict()
            )
            token_list = {"exchangeType": 2, "tokens": list(self.symbol_token.keys())}
            h = _random_broker()
            kwargs = dict(
                auth_token=h.access_token,
                api_key=h._api_key,
                client_code=h._user_id,
                feed_token=h.obj.feed_token,
            )
            self.ws = Wsocket(kwargs=kwargs, token=token_list)
            self.ws.daemon = True
            self.ws.start()


if __name__ == "__main__":
    try:
        monitor = Monitor()
        monitor.main()
        __import__("time").sleep(1)
    except KeyboardInterrupt as k:
        print("pressed ctrl c")
        monitor.ws.close_connection()
        monitor.ws.join()
        __import__("sys").exit()
