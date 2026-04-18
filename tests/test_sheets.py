import csv
import io
from unittest.mock import patch, MagicMock
from services.sheets import SheetsClient


_FIELDS = ["class_name", "start_date", "end_date", "city", "state", "price", "spots_left", "payment_link", "calendar_link", "active"]


def _make_csv(*rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=_FIELDS)
    writer.writeheader()
    for r in rows:
        writer.writerow(dict(zip(_FIELDS, r)))
    return buf.getvalue()


def _mock_response(text):
    mock = MagicMock()
    mock.text = text
    mock.raise_for_status = MagicMock()
    return mock


def test_get_active_classes_returns_active_only():
    csv_text = _make_csv(
        ["4-Day Epoxy Bootcamp", "2026-04-27", "2026-04-30", "Atlanta", "Georgia", "$2,500", 5, "https://pay.example.com", "https://cal.example.com", "TRUE"],
        ["Old Class", "2025-01-01", "2025-01-04", "Miami", "Florida", "$2,500", 0, "", "", "FALSE"],
    )
    with patch("services.sheets.requests.get", return_value=_mock_response(csv_text)):
        client = SheetsClient(csv_url="https://example.com/sheet.csv")
        classes = client.get_active_classes()

    assert len(classes) == 1
    assert classes[0].city == "Atlanta"
    assert classes[0].state == "Georgia"
    assert classes[0].spots_left == 5


def test_get_classes_for_state_filters_by_state():
    csv_text = _make_csv(
        ["Atlanta Bootcamp", "2026-04-27", "2026-04-30", "Atlanta", "Georgia", "$2,500", 3, "https://pay.example.com", "https://cal.example.com", "TRUE"],
        ["Miami Bootcamp", "2026-06-01", "2026-06-04", "Miami", "Florida", "$2,500", 8, "https://pay.example.com", "https://cal.example.com", "TRUE"],
    )
    with patch("services.sheets.requests.get", return_value=_mock_response(csv_text)):
        client = SheetsClient(csv_url="https://example.com/sheet.csv")
        classes = client.get_classes_for_state("Georgia")

    assert len(classes) == 1
    assert classes[0].city == "Atlanta"
