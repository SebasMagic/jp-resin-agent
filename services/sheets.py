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
            if str(r.get("active", "")).upper() != "TRUE":
                continue
            spots_raw = str(r.get("spots_left", "0")).strip()
            classes.append(ClassInfo(
                name=r["class_name"],
                start_date=r["start_date"],
                end_date=r["end_date"],
                city=r["city"],
                state=r["state"],
                price=str(r["price"]),
                spots_left=int(spots_raw) if spots_raw.isdigit() else 0,
                payment_link=r["payment_link"],
                calendar_link=r["calendar_link"],
            ))
        return classes

    def get_active_classes(self) -> list[ClassInfo]:
        return self._fetch_active()

    def get_classes_for_state(self, state: str) -> list[ClassInfo]:
        return [c for c in self._fetch_active() if c.state.lower() == state.lower()]
