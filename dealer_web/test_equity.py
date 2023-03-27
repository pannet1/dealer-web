import user
import pandas as pd


def get_high(symboltoken, fm=20):
    try:
        ao = user.random_broker()
        historicParam = {
            "exchange": "NSE",
            "symboltoken": symboltoken,
            "interval": "ONE_DAY",
            "fromdate": f"2023-03-{fm} 09:14",
            "todate": "2023-03-24 15:35",
        }
        resp = ao.obj.getCandleData(historicParam)
        print(f"response is {resp.get('data')}")
        if resp.get('data'):
            return resp.get('data')[:-1][0][2]
        else:
            return 0
    except Exception as e:
        print(e)
        return 0


class Equity:

    def __init__(self):
        user.contracts()
        self.df = pd.DataFrame()
        self.sleep = 1

    def set_symbols(self):
        lst_sym = ['SBIN', 'ITC']
        df = pd.DataFrame(columns=["symbol"], data=lst_sym)
        df['symboltoken'] = df.apply(user.get_token, axis=1)
        df['pdh'] = 0
        self.df = df

    def get_highs(self):
        df_cp = self.df.query("pdh==0")
        for i, row in df_cp.iterrows():
            self.df.loc[self.df.symbol == row.symbol,
                        "pdh"] = get_high(row.symboltoken, fm=22)


if __name__ == "__main__":
    e = Equity()
    e.set_symbols()
    while e.sleep < 3:
        leng = e.df.query("pdh==0")
        print(leng)
        while not leng.empty and e.sleep < 3:
            e.get_highs()
            time = __import__("time")
            time.sleep(e.sleep)
            print(e.sleep)
            e.sleep += 1
        else:
            continue
    SystemExit()
    e.sleep == 1
