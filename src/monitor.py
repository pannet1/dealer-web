from constants import alerts_json, futil, D_SETG
from pprint import pprint
from user import get_ltps, load_all_users, positions, _random_broker, get_broker_by_id
from user_helper import _order_place_by_user
from api_helper import get_tkn_fm_sym
import pandas as pd
from wsocket import Wsocket
from copy import deepcopy
from traceback import print_exc
from logzero import logger as logging
from typing import Any
from toolkit.telegram import Telegram


def convert_price(price: float):
    price = price / 100
    price = round(price / 0.05) * 0.05
    return str(price)


def split(tradingsymbol_to_be_split):
    if tradingsymbol_to_be_split.endswith("-EQ"):
        return tradingsymbol_to_be_split[:-3]
    elif tradingsymbol_to_be_split.endswith(" 50"):
        return tradingsymbol_to_be_split[:-3]
    else:
        return "STRING_IS_NOT_FOUND"


class Monitor:

    def _tkn_fm_alert(self) -> list:
        tokens = []
        for alert in self.alerts:
            # mutate
            alert["instrument_token"] = get_tkn_fm_sym(sym=alert["name"], exch="NSE")
            alert["ltp"] = None
            tokens.append(alert["instrument_token"])
        return tokens

    def _df_fm_positions(self) -> pd.DataFrame():
        df = pd.DataFrame()
        while df.empty:
            _, _, columns, data = positions()
            if data is not None and any(data):
                df = pd.DataFrame(data=data, columns=columns)
            __import__("time").sleep(2)
        df["token"] = None
        df["netqty"] = df["netqty"].astype(int)
        mask = (df["exchange"] == "NFO") & (df["netqty"] < 0)
        df.loc[mask, "token"] = df.loc[mask].apply(
            lambda row: get_tkn_fm_sym(row["tradingsymbol"], "NFO"), axis=1
        )
        return df

    def __init__(self):
        self.alerts: list = futil.read_file(alerts_json)["alerts"]
        self.users: list = load_all_users()
        self.equity_tokens: list = self._tkn_fm_alert()
        df = self._df_fm_positions()
        self.token_symbols = (
            df.dropna(subset=["token"]).set_index("token")["tradingsymbol"].to_dict()
        )
        token_list = {"exchangeType": 2, "tokens": list(self.token_symbols.keys())}
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
        self.tg = Telegram(D_SETG["telegram_api"], D_SETG["chat_id"])

    def _flatten_askbid(self):
        try:
            flattened_ticks = []
            ticks = self.ws.ticks
            copied_ticks = deepcopy(ticks)
            for token, v in copied_ticks.items():
                dct = dict(
                    tradingsymbol=self.token_symbols[token],
                    ask=min(item["price"] for item in v["best_5_buy_data"]),
                    bid=max(item["price"] for item in v["best_5_sell_data"]),
                )
                flattened_ticks.append(dct)

            for ticks in flattened_ticks:
                ask, bid = ticks["ask"], ticks["bid"]
                if ask == 0 or bid == 0:
                    ticks["is_trade"] = False
                    logging.warning(f'no tick for {ticks["tradingsymbol"]}')
                else:
                    ticks["is_trade"] = (
                        True if ((bid - ask) / ask * 100) < 20 else False
                    )
        except Exception as e:
            logging.error(f"{e} flatten askbid")
            print_exc()
        finally:
            return flattened_ticks

    def get_equity_ltp(self):
        try:
            resp = get_ltps("NSE", self.equity_tokens)
            for alert in self.alerts:
                alert["ltp"] = resp.get(alert["instrument_token"], None)
        except Exception as e:
            logging.error(f"{e} in get equity ltp")
            print_exc()

    def tokens_from_positions(self, action, df) -> dict[Any, Any]:
        """
        finds relevant option symbol and token
        from positions df
        """
        try:
            token_symbols = {}
            pfx = split(action["tradingsymbol"])
            ce_or_pe = action["action"]
            for _, position in df.iterrows():
                tsym = position["tradingsymbol"]
                if tsym.startswith(pfx) and ce_or_pe in tsym:
                    token = get_tkn_fm_sym(tsym, "NFO")
                    token = str(token)
                    token_symbols[token] = tsym
        except Exception as e:
            logging.info(f"{e} in option from action")
            print_exc()
        finally:
            return token_symbols

    def subscribe_till_ltp(self, token_symbols, askbid):
        position_symbol = list(token_symbols.values())
        subscribed = [item["tradingsymbol"] for item in askbid]
        if not all(option in position_symbol for option in subscribed):
            self.token_symbols.update(token_symbols)
            print(f"{self.token_symbols} \n subscribed")
            token_list = {"exchangeType": 2, "tokens": list(token_symbols.keys())}
            self.ws.subscribe(token_list)

    def find_actions(self, alert, event_type: str):
        # todo
        event_on_alert = []
        logging.info(f"ltp is {event_type} for {alert['name']}")
        # create a shallow copy
        for action in alert["actions"][:]:
            if action["event"] == event_type:
                action["tradingsymbol"] = alert["name"]
                event_on_alert.append(action)
                # safely remove from original
                alert["actions"].remove(action)
        return event_on_alert

    def main(self):
        try:
            action_objects = []
            while True:
                self.get_equity_ltp()
                for alert in self.alerts:
                    action_dicts = []
                    if alert["ltp"] > float(alert["above"]):
                        action_dicts = self.find_actions(alert, "above")
                    elif alert["ltp"] < float(alert["below"]):
                        action_dicts = self.find_actions(alert, "below")

                df = self._df_fm_positions()
                # find and delete actions
                token_symbols = []
                for action_dict in action_dicts:
                    pprint(action_dict)
                    token_symbols = self.tokens_from_positions(action_dict, df)
                    self.subscribe_till_ltp(token_symbols, self._flatten_askbid())

                # create ACTION object
                if any(token_symbols):
                    tradingsymbols = list(token_symbols.values())
                    for tradingsymbol in tradingsymbols:
                        action_objects.append(Action(tradingsymbol))

                # delete ACTION object
                action_objects = [obj for obj in action_objects if obj.enabled]

                # run
                for obj in action_objects:
                    askbid = self._flatten_askbid()
                    askbid = [
                        item
                        for item in askbid
                        if item["is_trade"] == True
                        and item["tradingsymbol"] == obj.tradingsymbol
                    ]
                    if any(askbid):
                        flattened_df = pd.DataFrame(askbid)
                        merged_df = pd.merge(
                            df, flattened_df, on="tradingsymbol", how="inner"
                        )
                        obj.run(df=merged_df)
                    else:
                        logging.warning(f"ask/bid is wide {obj.tradingsymbol} ")
                __import__("time").sleep(1)

        except KeyboardInterrupt:
            __import__("sys").exit(1)
            print("interruped via keyboard")
        except Exception as e:
            print(f"{e} in main loop")
            print_exc()


class Action:
    def __init__(self, tradingsymbol):
        self.enabled = True
        self.tradingsymbol = tradingsymbol
        print("from alert oject", tradingsymbol)

    def run(self, df):
        if not df.empty:
            for _, row in df.iterrows():
                resp = self.cover_positions(row)
                print(f"{resp=} received while covering position")

    def cover_positions(self, row):
        params = {
            "tradingsymbol": row["tradingsymbol"],
            "symboltoken": row["token"],
            "transactiontype": "BUY",
            "exchange": row["exchange"],
            "price": convert_price(row["bid"]),
            "triggerprice": "0",
            # update
            "quantity": str(abs(row["netqty"])),
            "ordertype": "LIMIT",
            "producttype": row["producttype"],
            "variety": "NORMAL",
            "duration": "DAY",
        }
        client = row["client_name"]
        return _order_place_by_user(get_broker_by_id(client), params)


if __name__ == "__main__":
    try:
        monitor = Monitor()
        monitor.main()
    except KeyboardInterrupt:
        print("pressed ctrl c")
        monitor.ws.close_connection()
        monitor.ws.join()
__import__("sys").exit()
