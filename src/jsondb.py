import json
from typing import Optional
from toolkit.fileutils import Fileutils


class JsonDB:
    def __init__(self, file_path: str):
        self.fileutils = Fileutils()
        self.path = file_path
        self.data = {"alerts": []}
        self.load()

    def load(self):
        try:
            if self.fileutils.is_file_exists(self.path) is False:
                self.fileutils.write_file(self.path, self.data)
            else:
                self.data = self.fileutils.json_fm_file(self.path)
        except Exception as e:
            print(f"while loading {e}")
        finally:
            self.enumerate_ids()

    def save(self):
        try:
            self.enumerate_ids()
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"while saving {e}")

    def enumerate_ids(self):
        for i, alert in enumerate(self.data["alerts"], 1):
            alert["id"] = i
            for j, action in enumerate(alert.get("actions", []), 1):
                action["id"] = j

    def get_alerts(self):
        return self.data["alerts"]

    def get_alert(self, alert_id: int) -> Optional[dict]:
        return next((a for a in self.data["alerts"] if a["id"] == alert_id), None)

    def add_alert(self, name: str, above: str, below: str, price: str):
        self.data["alerts"].append(
            {
                "id": 0,  # will be re-enumerated
                "name": name,
                "above": above,
                "below": below,
                "price": float(price),
                "actions": [],
            }
        )
        self.save()

    def delete_alert(self, alert_id: int):
        self.data["alerts"] = [a for a in self.data["alerts"] if a["id"] != alert_id]
        self.save()

    def add_action(self, alert_id: int, event: str, action: str):
        alert = self.get_alert(alert_id)
        if alert is not None:
            alert["actions"].append(
                {
                    "id": 0,  # will be re-enumerated
                    "event": event,
                    "action": action,
                }
            )
            self.save()

    def delete_action(self, alert_id: int, action_id: int):
        alert = self.get_alert(alert_id)
        if alert is not None:
            alert["actions"] = [a for a in alert["actions"] if a["id"] != action_id]
            self.save()
