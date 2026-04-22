import csv
import io
import requests
from models.lead import ClassInfo


class SheetsClient:
    def __init__(self, csv_url: str):
        self._csv_url = csv_url

    def _fetch_active(self) -> list[ClassInfo]:
        response = requests.get(self._csv_url, timeout=10)
        response.raise_for_status()
        reader = csv.DictReader(io.StringIO(response.text))
        classes = []
        for r in reader:
            spots_raw = str(r.get("Spots Left Real", "0")).strip()
            spots = int(spots_raw) if spots_raw.isdigit() else 0
            if spots <= 0:
                continue
            classes.append(ClassInfo(
                name=r.get("Job Type", ""),
                start_date=r.get("Class Starts", ""),
                end_date=r.get("Class Ends", ""),
                city=r.get("City", ""),
                state=r.get("State", ""),
                price="",
                spots_left=spots,
                payment_link=r.get("Stripe Link", ""),
                calendar_link="",
            ))
        return classes

    def get_active_classes(self) -> list[ClassInfo]:
        return self._fetch_active()

    def get_classes_for_state(self, state: str) -> list[ClassInfo]:
        return [c for c in self._fetch_active() if c.state.lower() == state.lower()]
