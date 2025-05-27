from constants import alerts_json, futil
from pprint import pprint
from user import load_all_users


class Monitor:
    def __init__(self):
        resp = futil.read_file(alerts_json)
        self.equities = [alert["name"] for alert in resp["alerts"]]
        self.json_file = futil.read_file(alerts_json)
        self.users = load_all_users()

    def _update_equity_ltp(self):

        # get random broker
        return resp

    def run(self):
        self._update_equity_ltp()
        for alert in self.json_file["alerts"]:
            if alert["ltp"] > alert["above"] or alert["ltp"] < alert["below"]:
                print("send alert")


if __name__ == "__main__":
    monitor = Monitor()
    while True:
        monitor.run()
