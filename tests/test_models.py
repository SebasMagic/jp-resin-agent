# tests/test_models.py
from models.lead import LeadForm, LeadScore, LeadType


def test_lead_type_values():
    assert LeadType.HOT == "hot"
    assert LeadType.MID == "mid"
    assert LeadType.COLD == "cold"


def test_lead_form_parses_state():
    form = LeadForm(
        contact_id="abc123",
        first_name="John",
        last_name="Doe",
        email="john@test.com",
        phone="+1234567890",
        state="Georgia",
        experience="Yes, I do flooring/construction work now",
        goal="Start my own epoxy business and go full-time",
        investment="I'm ready to commit and start ASAP",
        channel="SMS",
    )
    assert form.state == "Georgia"
    assert form.contact_id == "abc123"


def test_lead_score_classification():
    score = LeadScore(
        experience_pts=10,
        goal_pts=30,
        investment_pts=40,
        location_pts=20,
    )
    assert score.total == 100
    assert score.lead_type == LeadType.HOT


def test_lead_score_mid():
    score = LeadScore(
        experience_pts=6,
        goal_pts=10,
        investment_pts=25,
        location_pts=0,
    )
    assert score.total == 41
    assert score.lead_type == LeadType.MID


def test_lead_score_cold():
    score = LeadScore(
        experience_pts=3,
        goal_pts=5,
        investment_pts=5,
        location_pts=0,
    )
    assert score.total == 13
    assert score.lead_type == LeadType.COLD
