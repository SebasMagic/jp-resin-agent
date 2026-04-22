import httpx
from typing import Any


GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"

CHANNEL_TYPE_MAP = {
    "sms": "SMS",
    "instagram": "IG",
    "ig": "IG",
    "facebook": "FB",
    "fb": "FB",
    "facebook_messenger": "FB",
}


class GHLClient:
    def __init__(self, pit_token: str, location_id: str):
        self._headers = {
            "Authorization": f"Bearer {pit_token}",
            "Version": GHL_VERSION,
            "Content-Type": "application/json",
        }
        self._location_id = location_id

    def _get(self, path: str, params: dict = None) -> dict:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(f"{GHL_BASE}{path}", headers=self._headers, params=params)
            resp.raise_for_status()
            return resp.json()

    def _post(self, path: str, body: dict) -> dict:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(f"{GHL_BASE}{path}", headers=self._headers, json=body)
            resp.raise_for_status()
            return resp.json()

    def _put(self, path: str, body: dict) -> dict:
        with httpx.Client(timeout=30.0) as client:
            resp = client.put(f"{GHL_BASE}{path}", headers=self._headers, json=body)
            resp.raise_for_status()
            return resp.json()

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        data = self._get(f"/contacts/{contact_id}")
        return data["contact"]

    def send_message(self, contact_id: str, message: str, channel: str = "SMS") -> dict:
        msg_type = CHANNEL_TYPE_MAP.get(channel.lower(), "SMS")
        body = {"type": msg_type, "contactId": contact_id, "message": message}
        return self._post("/conversations/messages", body)

    def create_opportunity(self, contact_id: str, pipeline_id: str, stage_id: str, name: str) -> dict:
        body = {
            "pipelineId": pipeline_id,
            "locationId": self._location_id,
            "name": name.strip() or "New Lead",
            "pipelineStageId": stage_id,
            "status": "open",
            "contactId": contact_id,
        }
        data = self._post("/opportunities", body)
        return data["opportunity"]

    def update_opportunity_stage(self, opportunity_id: str, stage_id: str) -> dict:
        data = self._put(f"/opportunities/{opportunity_id}", {"pipelineStageId": stage_id})
        return data["opportunity"]

    def create_task(self, contact_id: str, title: str) -> dict:
        body = {"title": title, "dueDate": "", "completed": False}
        data = self._post(f"/contacts/{contact_id}/tasks", body)
        return data["task"]

    def trigger_workflow(self, contact_id: str, workflow_id: str) -> dict:
        body = {"workflowId": workflow_id}
        return self._post(f"/contacts/{contact_id}/workflow", body)

    def get_pipelines(self) -> list[dict]:
        data = self._get("/opportunities/pipelines", params={"locationId": self._location_id})
        return data["pipelines"]

    def get_custom_fields(self) -> list[dict]:
        data = self._get(f"/locations/{self._location_id}/customFields")
        return data["customFields"]

    def search_opportunities(self, contact_id: str, pipeline_id: str = "") -> list[dict]:
        params = {"contactId": contact_id, "locationId": self._location_id}
        if pipeline_id:
            params["pipelineId"] = pipeline_id
        try:
            data = self._get("/opportunities/search", params=params)
            return data.get("opportunities", [])
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (404, 422):
                return []
            raise
