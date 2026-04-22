import csv
import io
from unittest.mock import patch, MagicMock
from services.sheets import SheetsClient


_FIELDS = ["Class Starts", "Class Ends", "City", "State", "Job Type", "Stripe Link", "Spots Left Real", "Spots Left Scarcity"]


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


def test_get_active_classes_returns_rows_with_spots():
    csv_text = _make_csv(
        ["27 April", "30 April", "Atlanta", "Georgia", "Job Site", "https://pay.example.com", 5, 2],
        ["01 June", "04 June", "Miami", "Florida", "Job Site", "https://pay2.example.com", 0, 0],
    )
    with patch("services.sheets.requests.get", return_value=_mock_response(csv_text)):
        client = SheetsClient(csv_url="https://example.com/sheet.csv")
        classes = client.get_active_classes()

    assert len(classes) == 1
    assert classes[0].city == "Atlanta"
    assert classes[0].state == "Georgia"
    assert classes[0].spots_left == 5
    assert classes[0].payment_link == "https://pay.example.com"


def test_get_classes_for_state_filters_by_state():
    csv_text = _make_csv(
        ["27 April", "30 April", "Atlanta", "Georgia", "Job Site", "https://pay.example.com", 3, 1],
        ["01 June", "04 June", "Miami", "Florida", "Job Site", "https://pay2.example.com", 8, 5],
    )
    with patch("services.sheets.requests.get", return_value=_mock_response(csv_text)):
        client = SheetsClient(csv_url="https://example.com/sheet.csv")
        classes = client.get_classes_for_state("Georgia")

    assert len(classes) == 1
    assert classes[0].city == "Atlanta"
