# tests/test_ghl.py
import pytest
import respx
import httpx
from services.ghl import GHLClient


GHL_BASE = "https://services.leadconnectorhq.com"


@pytest.fixture
def client():
    return GHLClient(pit_token="test-token", location_id="loc123")


@respx.mock
def test_get_contact(client):
    respx.get(f"{GHL_BASE}/contacts/contact123").mock(
        return_value=httpx.Response(200, json={"contact": {"id": "contact123", "firstName": "John"}})
    )
    result = client.get_contact("contact123")
    assert result["id"] == "contact123"
    assert result["firstName"] == "John"


@respx.mock
def test_send_message(client):
    respx.post(f"{GHL_BASE}/conversations/messages").mock(
        return_value=httpx.Response(200, json={"id": "msg123"})
    )
    result = client.send_message(contact_id="contact123", message="Hello!", channel="SMS")
    assert result["id"] == "msg123"


@respx.mock
def test_create_opportunity(client):
    respx.post(f"{GHL_BASE}/opportunities").mock(
        return_value=httpx.Response(200, json={"opportunity": {"id": "opp123"}})
    )
    result = client.create_opportunity(
        contact_id="contact123",
        pipeline_id="pipe123",
        stage_id="stage123",
        name="John Doe",
    )
    assert result["id"] == "opp123"


@respx.mock
def test_update_opportunity_stage(client):
    respx.put(f"{GHL_BASE}/opportunities/opp123").mock(
        return_value=httpx.Response(200, json={"opportunity": {"id": "opp123", "pipelineStageId": "stage456"}})
    )
    result = client.update_opportunity_stage(opportunity_id="opp123", stage_id="stage456")
    assert result["id"] == "opp123"


@respx.mock
def test_create_task(client):
    respx.post(f"{GHL_BASE}/contacts/contact123/tasks").mock(
        return_value=httpx.Response(200, json={"task": {"id": "task123"}})
    )
    result = client.create_task(contact_id="contact123", title="Call this lead NOW - HOT")
    assert result["id"] == "task123"


@respx.mock
def test_trigger_workflow(client):
    respx.post(f"{GHL_BASE}/contacts/contact123/workflow").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = client.trigger_workflow(contact_id="contact123", workflow_id="wf123")
    assert result["success"] is True


@respx.mock
def test_get_pipelines(client):
    respx.get(f"{GHL_BASE}/opportunities/pipelines").mock(
        return_value=httpx.Response(200, json={"pipelines": [{"id": "pipe1", "name": "JP Resin"}]})
    )
    result = client.get_pipelines()
    assert len(result) == 1
    assert result[0]["name"] == "JP Resin"


@respx.mock
def test_get_custom_fields(client):
    respx.get(f"{GHL_BASE}/locations/loc123/customFields").mock(
        return_value=httpx.Response(200, json={"customFields": [{"id": "f1", "name": "experience"}]})
    )
    result = client.get_custom_fields()
    assert result[0]["name"] == "experience"
