# tests/test_sheets.py
from unittest.mock import MagicMock, patch
from services.sheets import SheetsClient
from models.lead import ClassInfo


def _make_mock_worksheet(rows):
    ws = MagicMock()
    ws.get_all_records.return_value = rows
    return ws


def test_get_active_classes_returns_active_only():
    rows = [
        {
            "class_name": "4-Day Epoxy Bootcamp",
            "start_date": "2026-04-27",
            "end_date": "2026-04-30",
            "city": "Atlanta",
            "state": "Georgia",
            "price": "$2,500",
            "spots_left": 5,
            "payment_link": "https://pay.example.com",
            "calendar_link": "https://cal.example.com",
            "active": "TRUE",
        },
        {
            "class_name": "Old Class",
            "start_date": "2025-01-01",
            "end_date": "2025-01-04",
            "city": "Miami",
            "state": "Florida",
            "price": "$2,500",
            "spots_left": 0,
            "payment_link": "",
            "calendar_link": "",
            "active": "FALSE",
        },
    ]
    with patch("services.sheets.gspread") as mock_gspread:
        mock_client = MagicMock()
        mock_gspread.service_account_from_dict.return_value = mock_client
        mock_client.open_by_key.return_value.sheet1 = _make_mock_worksheet(rows)

        client = SheetsClient(service_account_json="{}", sheet_id="sheet123")
        classes = client.get_active_classes()

    assert len(classes) == 1
    assert classes[0].city == "Atlanta"
    assert classes[0].state == "Georgia"
    assert classes[0].spots_left == 5


def test_get_classes_for_state_filters_by_state():
    rows = [
        {
            "class_name": "Atlanta Bootcamp",
            "start_date": "2026-04-27",
            "end_date": "2026-04-30",
            "city": "Atlanta",
            "state": "Georgia",
            "price": "$2,500",
            "spots_left": 3,
            "payment_link": "https://pay.example.com",
            "calendar_link": "https://cal.example.com",
            "active": "TRUE",
        },
        {
            "class_name": "Miami Bootcamp",
            "start_date": "2026-06-01",
            "end_date": "2026-06-04",
            "city": "Miami",
            "state": "Florida",
            "price": "$2,500",
            "spots_left": 8,
            "payment_link": "https://pay.example.com",
            "calendar_link": "https://cal.example.com",
            "active": "TRUE",
        },
    ]
    with patch("services.sheets.gspread") as mock_gspread:
        mock_client = MagicMock()
        mock_gspread.service_account_from_dict.return_value = mock_client
        mock_client.open_by_key.return_value.sheet1 = _make_mock_worksheet(rows)

        client = SheetsClient(service_account_json="{}", sheet_id="sheet123")
        classes = client.get_classes_for_state("Georgia")

    assert len(classes) == 1
    assert classes[0].city == "Atlanta"
