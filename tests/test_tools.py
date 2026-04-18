# tests/test_tools.py
from unittest.mock import MagicMock
from agent.tools import build_tools
from models.lead import ClassInfo


def _make_deps():
    ghl = MagicMock()
    sheets = MagicMock()
    store = MagicMock()
    settings = MagicMock()
    settings.GHL_PIPELINE_ID = "pipe1"
    settings.GHL_STAGE_HOT = "stage_hot"
    settings.GHL_STAGE_MID = "stage_mid"
    settings.GHL_STAGE_COLD = "stage_cold"
    settings.GHL_STAGE_IN_CONVERSATION = "stage_convo"
    settings.GHL_STAGE_CALL_SCHEDULED = "stage_call"
    settings.GHL_STAGE_ENROLLED = "stage_enrolled"
    settings.GHL_STAGE_NOT_INTERESTED = "stage_ni"
    settings.GHL_WORKFLOW_NURTURE_ROI = "wf_roi"
    settings.GHL_WORKFLOW_NURTURE_CLASS_INFO = "wf_class"
    settings.GHL_WORKFLOW_FOLLOWUP_HOT = "wf_hot"
    settings.GHL_WORKFLOW_FOLLOWUP_MID = "wf_mid"
    settings.GHL_WORKFLOW_FOLLOWUP_COLD = "wf_cold"
    return ghl, sheets, store, settings


def test_build_tools_returns_list():
    ghl, sheets, store, settings = _make_deps()
    tools = build_tools(contact_id="c1", ghl=ghl, sheets=sheets, store=store, settings=settings)
    tool_names = [t.name for t in tools]
    assert "move_pipeline" in tool_names
    assert "send_message" in tool_names
    assert "get_classes" in tool_names
    assert "notify_jp" in tool_names
    assert "send_payment_link" in tool_names
    assert "send_calendar_link" in tool_names
    assert "trigger_workflow" in tool_names


def test_move_pipeline_calls_ghl():
    ghl, sheets, store, settings = _make_deps()
    ghl.search_opportunities.return_value = [{"id": "opp1"}]
    tools = build_tools(contact_id="c1", ghl=ghl, sheets=sheets, store=store, settings=settings)
    move = next(t for t in tools if t.name == "move_pipeline")
    move.invoke({"stage": "hot"})
    ghl.update_opportunity_stage.assert_called_once_with("opp1", "stage_hot")


def test_send_message_calls_ghl():
    ghl, sheets, store, settings = _make_deps()
    tools = build_tools(contact_id="c1", ghl=ghl, sheets=sheets, store=store, settings=settings)
    send = next(t for t in tools if t.name == "send_message")
    send.invoke({"message": "Hello!", "channel": "SMS"})
    ghl.send_message.assert_called_once_with(contact_id="c1", message="Hello!", channel="SMS")


def test_get_classes_returns_formatted_string():
    ghl, sheets, store, settings = _make_deps()
    sheets.get_active_classes.return_value = [
        ClassInfo(
            name="Atlanta Bootcamp",
            start_date="2026-04-27",
            end_date="2026-04-30",
            city="Atlanta",
            state="Georgia",
            price="$2,500",
            spots_left=3,
            payment_link="https://pay.com",
            calendar_link="https://cal.com",
        )
    ]
    tools = build_tools(contact_id="c1", ghl=ghl, sheets=sheets, store=store, settings=settings)
    get_classes = next(t for t in tools if t.name == "get_classes")
    result = get_classes.invoke({})
    assert "Atlanta" in result
    assert "3 spots" in result
