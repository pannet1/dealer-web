from constants import alerts_json, futil
from pprint import pprint


def extract_alert_symbols():
    resp = futil.read_file(alerts_json)
    return [alert["name"]
    for alert in resp["alerts"]]

def _update_equity_ltp(equities):
    #get random broker
    return {}

def update_alert_ltp(equities, resp):
    equities = _update_equity_ltp(equities)
    return resp 

if __name__ == "__main__":
    equities: list = extract_alert_symbols()
    resp = futil.read_file(alerts_json)
    while True:
        resp = update_alert_ltp(equities, resp)
        for alert in resp["alerts"]:
            if alert["ltp"] > alert["above"] or alert["ltp"] < alert["below"]:
                print("send alert")
        

    
