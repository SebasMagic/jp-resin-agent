# tests/test_scorer.py
from agent.scorer import score_lead
from models.lead import LeadForm, LeadScore, LeadType


def _make_form(**kwargs):
    defaults = {
        "contact_id": "c1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@test.com",
        "phone": "+1234567890",
        "state": "Georgia",
        "experience": "Yes, I do flooring/construction work now",
        "goal": "Start my own epoxy business and go full-time",
        "investment": "I'm ready to commit and start ASAP",
        "channel": "SMS",
    }
    defaults.update(kwargs)
    return LeadForm(**defaults)


def test_perfect_score_hot_georgia():
    form = _make_form()
    active_states = ["Georgia"]
    result = score_lead(form, active_states)
    assert result.experience_pts == 10
    assert result.goal_pts == 30
    assert result.investment_pts == 40
    assert result.location_pts == 20
    assert result.total == 100
    assert result.lead_type == LeadType.HOT


def test_no_location_match_reduces_score():
    form = _make_form(state="Texas")
    result = score_lead(form, ["Georgia"])
    assert result.location_pts == 0
    assert result.total == 80
    assert result.lead_type == LeadType.HOT


def test_mid_lead():
    form = _make_form(
        goal="Learn as a hobby or side hustle",
        investment="Within the next 1-3 months",
        experience="I've done some DIY projects at home",
        state="Texas",
    )
    result = score_lead(form, ["Georgia"])
    assert result.goal_pts == 10
    assert result.investment_pts == 25
    assert result.experience_pts == 6
    assert result.location_pts == 0
    assert result.total == 41
    assert result.lead_type == LeadType.MID


def test_cold_lead():
    form = _make_form(
        goal="Just exploring options right now",
        investment="Just gathering info for now",
        experience="No experience at all, just researching",
        state="Texas",
    )
    result = score_lead(form, ["Georgia"])
    assert result.total == 13
    assert result.lead_type == LeadType.COLD


def test_unknown_answer_scores_zero():
    form = _make_form(goal="Something not in the list")
    result = score_lead(form, ["Georgia"])
    assert result.goal_pts == 0
