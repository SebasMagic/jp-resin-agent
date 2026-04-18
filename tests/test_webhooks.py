# tests/test_webhooks.py
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def _new_lead_payload():
    return {
        "type": "ContactCreate",
        "locationId": "AWQqYSyxdYeqqhoLc0ef",
        "contact": {
            "id": "contact123",
            "firstName": "John",
            "lastName": "Doe",
            "email": "john@test.com",
            "phone": "+14045551234",
            "state": "Georgia",
            "customFields": [
                {"id": "field_exp", "value": "Yes, I do flooring/construction work now"},
                {"id": "field_goal", "value": "Start my own epoxy business and go full-time"},
                {"id": "field_inv", "value": "I'm ready to commit and start ASAP"},
            ],
        },
    }


def test_health():
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("main.GHLClient")
@patch("main.SheetsClient")
@patch("main.ConversationStore")
@patch("main.score_lead")
@patch("main.run_agent")
def test_new_lead_webhook_returns_200(mock_agent, mock_score, mock_store, mock_sheets, mock_ghl):
    from models.lead import LeadScore, LeadType
    mock_score.return_value = LeadScore(experience_pts=10, goal_pts=30, investment_pts=40, location_pts=20)
    mock_agent.return_value = "Message sent"
    mock_sheets_instance = MagicMock()
    mock_sheets_instance.get_active_classes.return_value = []
    mock_sheets.return_value = mock_sheets_instance
    mock_ghl_instance = MagicMock()
    mock_ghl_instance.search_opportunities.return_value = []
    mock_ghl_instance.create_opportunity.return_value = {"id": "opp123"}
    mock_ghl.return_value = mock_ghl_instance
    mock_store_instance = MagicMock()
    mock_store.return_value = mock_store_instance

    from main import app
    client = TestClient(app)
    resp = client.post(
        "/webhook/new-lead",
        json=_new_lead_payload(),
        headers={"x-webhook-secret": "changeme"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "processed"
    assert resp.json()["lead_type"] in ["hot", "mid", "cold"]


@patch("main.GHLClient")
@patch("main.SheetsClient")
@patch("main.ConversationStore")
@patch("main.run_agent")
def test_reply_webhook_returns_200(mock_agent, mock_store, mock_sheets, mock_ghl):
    mock_agent.return_value = "Reply sent"
    mock_store_instance = MagicMock()
    mock_store_instance.get_context.return_value = {
        "first_name": "John",
        "last_name": "Doe",
        "state": "Georgia",
        "lead_type": "hot",
        "score": 100,
        "experience": "Yes, I do flooring/construction work now",
        "goal": "Start my own epoxy business and go full-time",
        "investment": "I'm ready to commit and start ASAP",
    }
    mock_store.return_value = mock_store_instance
    mock_sheets_instance = MagicMock()
    mock_sheets_instance.get_active_classes.return_value = []
    mock_sheets.return_value = mock_sheets_instance

    from main import app
    client = TestClient(app)
    resp = client.post(
        "/webhook/reply",
        json={"contactId": "contact123", "message": "I'm interested!", "channel": "SMS"},
        headers={"x-webhook-secret": "changeme"},
    )
    assert resp.status_code == 200


def test_new_lead_webhook_rejects_wrong_secret():
    from main import app
    client = TestClient(app)
    resp = client.post(
        "/webhook/new-lead",
        json=_new_lead_payload(),
        headers={"x-webhook-secret": "wrongsecret"},
    )
    assert resp.status_code == 403


def test_new_lead_rejects_missing_secret():
    from main import app
    client = TestClient(app)
    resp = client.post("/webhook/new-lead", json=_new_lead_payload())
    assert resp.status_code == 403


def test_reply_rejects_missing_secret():
    from main import app
    client = TestClient(app)
    resp = client.post(
        "/webhook/reply",
        json={"contactId": "contact123", "message": "Hi", "channel": "SMS"},
    )
    assert resp.status_code == 403
