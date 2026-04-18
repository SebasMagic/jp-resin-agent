import gspread
from models.lead import ClassInfo


class SheetsClient:
    def __init__(self, service_account_json: str, sheet_id: str):
        import json
        creds_dict = json.loads(service_account_json)
        gc = gspread.service_account_from_dict(creds_dict)
        self._sheet = gc.open_by_key(sheet_id).sheet1

    def _fetch_active(self) -> list[ClassInfo]:
        rows = self._sheet.get_all_records()
        return [
            ClassInfo(
                name=r["class_name"],
                start_date=r["start_date"],
                end_date=r["end_date"],
                city=r["city"],
                state=r["state"],
                price=str(r["price"]),
                spots_left=int(r["spots_left"]) if str(r.get("spots_left", "0")).strip().isdigit() else 0,
                payment_link=r["payment_link"],
                calendar_link=r["calendar_link"],
            )
            for r in rows
            if str(r.get("active", "")).upper() == "TRUE"
        ]

    def get_active_classes(self) -> list[ClassInfo]:
        return self._fetch_active()

    def get_classes_for_state(self, state: str) -> list[ClassInfo]:
        return [c for c in self._fetch_active() if c.state.lower() == state.lower()]
