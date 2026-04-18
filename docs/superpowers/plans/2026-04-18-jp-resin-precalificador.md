# JP Resin Precalificador — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI + LangChain agent that recibe leads de GHL, calcula engagement score, mueve el pipeline y conversa con los leads vía SMS/Instagram/Facebook para convertirlos en inscritos al bootcamp JP Resin.

**Architecture:** FastAPI expone dos webhooks: uno para nuevos leads del form y otro para respuestas en conversación. Cada webhook dispara un LangChain ReAct agent con tools que envuelven el GHL API y Google Sheets API. La memoria conversacional se persiste por `contact_id` en SQLite.

**Tech Stack:** Python 3.11, FastAPI, LangChain 0.2, langchain-openai (DeepSeek via OpenAI-compatible API), gspread, httpx, SQLite, pytest, Render.

---

## File Map

```
jp-resin-agent/
├── main.py                    # FastAPI app, webhook endpoints
├── config.py                  # Settings via pydantic-settings
├── models/
│   └── lead.py                # LeadForm, LeadScore, LeadType (Pydantic)
├── services/
│   ├── ghl.py                 # GHL API v2 async client
│   └── sheets.py              # Google Sheets reader (gspread)
├── agent/
│   ├── scorer.py              # Pure engagement scoring function
│   ├── memory.py              # SQLite-backed conversation memory
│   ├── tools.py               # LangChain @tool definitions
│   ├── prompts.py             # System prompts per lead type
│   └── agent.py               # AgentExecutor factory
├── scripts/
│   └── fetch_ghl_ids.py       # One-time script: fetch pipeline/field IDs
├── tests/
│   ├── test_scorer.py
│   ├── test_ghl.py
│   ├── test_sheets.py
│   ├── test_memory.py
│   ├── test_tools.py
│   └── test_webhooks.py
├── requirements.txt
├── .env.example
└── render.yaml
```

---

## Task 1: Project Scaffold + Config

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `.env.example`
- Create: `render.yaml`
- Create: `main.py` (skeleton)

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.7.4
pydantic-settings==2.3.4
langchain==0.2.16
langchain-openai==0.1.25
langchain-community==0.2.16
httpx==0.27.2
gspread==6.1.2
google-auth==2.30.0
python-dotenv==1.0.1
pytest==8.3.2
pytest-asyncio==0.23.8
respx==0.21.1
```

- [ ] **Step 2: Create config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    GHL_PIT_TOKEN: str
    GHL_LOCATION_ID: str
    GHL_PIPELINE_ID: str = ""
    GHL_STAGE_NEW_LEAD: str = ""
    GHL_STAGE_HOT: str = ""
    GHL_STAGE_MID: str = ""
    GHL_STAGE_COLD: str = ""
    GHL_STAGE_IN_CONVERSATION: str = ""
    GHL_STAGE_CALL_SCHEDULED: str = ""
    GHL_STAGE_ENROLLED: str = ""
    GHL_STAGE_NOT_INTERESTED: str = ""

    GHL_FIELD_EXPERIENCE: str = ""
    GHL_FIELD_GOAL: str = ""
    GHL_FIELD_INVESTMENT: str = ""

    GHL_WORKFLOW_NURTURE_ROI: str = ""
    GHL_WORKFLOW_NURTURE_CLASS_INFO: str = ""
    GHL_WORKFLOW_FOLLOWUP_HOT: str = ""
    GHL_WORKFLOW_FOLLOWUP_MID: str = ""
    GHL_WORKFLOW_FOLLOWUP_COLD: str = ""

    DEEPSEEK_API_KEY: str

    GOOGLE_SHEETS_ID: str
    GOOGLE_SERVICE_ACCOUNT_JSON: str

    WEBHOOK_SECRET: str = "changeme"

    DB_PATH: str = "conversations.db"


settings = Settings()
```

- [ ] **Step 3: Create .env.example**

```
GHL_PIT_TOKEN=pit-434e3525-02b4-4960-a9e2-fc3f58d4d0fb
GHL_LOCATION_ID=AWQqYSyxdYeqqhoLc0ef
GHL_PIPELINE_ID=
GHL_STAGE_NEW_LEAD=
GHL_STAGE_HOT=
GHL_STAGE_MID=
GHL_STAGE_COLD=
GHL_STAGE_IN_CONVERSATION=
GHL_STAGE_CALL_SCHEDULED=
GHL_STAGE_ENROLLED=
GHL_STAGE_NOT_INTERESTED=
GHL_FIELD_EXPERIENCE=
GHL_FIELD_GOAL=
GHL_FIELD_INVESTMENT=
GHL_WORKFLOW_NURTURE_ROI=
GHL_WORKFLOW_NURTURE_CLASS_INFO=
GHL_WORKFLOW_FOLLOWUP_HOT=
GHL_WORKFLOW_FOLLOWUP_MID=
GHL_WORKFLOW_FOLLOWUP_COLD=
DEEPSEEK_API_KEY=
GOOGLE_SHEETS_ID=1p0avMlP5xFm1nWj2CkYD0ream60Ot4ed7qdzdvskqmI
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
WEBHOOK_SECRET=changeme
DB_PATH=conversations.db
```

- [ ] **Step 4: Create render.yaml**

```yaml
services:
  - type: web
    name: jp-resin-agent
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

- [ ] **Step 5: Create main.py skeleton**

```python
from fastapi import FastAPI

app = FastAPI(title="JP Resin Precalificador")


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Install dependencies and verify**

```bash
cd "jp-resin-agent"
pip install -r requirements.txt
uvicorn main:app --reload
```

Expected: server starts, `GET /health` returns `{"status": "ok"}`

- [ ] **Step 7: Commit**

```bash
git init
git add .
git commit -m "feat: project scaffold, config, requirements"
```

---

## Task 2: Pydantic Models

**Files:**
- Create: `models/__init__.py`
- Create: `models/lead.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError` — models not defined yet.

- [ ] **Step 3: Create models/__init__.py (empty)**

```python
```

- [ ] **Step 4: Create models/lead.py**

```python
from enum import Enum
from pydantic import BaseModel, computed_field


class LeadType(str, Enum):
    HOT = "hot"
    MID = "mid"
    COLD = "cold"


class LeadForm(BaseModel):
    contact_id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    state: str
    experience: str
    goal: str
    investment: str
    channel: str = "SMS"


class ClassInfo(BaseModel):
    name: str
    start_date: str
    end_date: str
    city: str
    state: str
    price: str
    spots_left: int
    payment_link: str
    calendar_link: str


class LeadScore(BaseModel):
    experience_pts: int
    goal_pts: int
    investment_pts: int
    location_pts: int

    @computed_field
    @property
    def total(self) -> int:
        return self.experience_pts + self.goal_pts + self.investment_pts + self.location_pts

    @computed_field
    @property
    def lead_type(self) -> LeadType:
        if self.total >= 70:
            return LeadType.HOT
        if self.total >= 40:
            return LeadType.MID
        return LeadType.COLD
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add models/ tests/test_models.py
git commit -m "feat: pydantic models for lead, score, lead type"
```

---

## Task 3: GHL API Client

**Files:**
- Create: `services/__init__.py`
- Create: `services/ghl.py`
- Create: `tests/test_ghl.py`

- [ ] **Step 1: Write failing tests**

```python
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
    respx.post(f"{GHL_BASE}/opportunities/").mock(
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_ghl.py -v
```

Expected: `ModuleNotFoundError` — service not defined yet.

- [ ] **Step 3: Create services/__init__.py (empty)**

```python
```

- [ ] **Step 4: Create services/ghl.py**

```python
import httpx
from typing import Any


GHL_BASE = "https://services.leadconnectorhq.com"
GHL_VERSION = "2021-07-28"

CHANNEL_TYPE_MAP = {
    "SMS": "SMS",
    "Instagram": "IG",
    "Facebook": "FB",
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
        with httpx.Client() as client:
            resp = client.get(f"{GHL_BASE}{path}", headers=self._headers, params=params)
            resp.raise_for_status()
            return resp.json()

    def _post(self, path: str, body: dict) -> dict:
        with httpx.Client() as client:
            resp = client.post(f"{GHL_BASE}{path}", headers=self._headers, json=body)
            resp.raise_for_status()
            return resp.json()

    def _put(self, path: str, body: dict) -> dict:
        with httpx.Client() as client:
            resp = client.put(f"{GHL_BASE}{path}", headers=self._headers, json=body)
            resp.raise_for_status()
            return resp.json()

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        data = self._get(f"/contacts/{contact_id}")
        return data["contact"]

    def send_message(self, contact_id: str, message: str, channel: str = "SMS") -> dict:
        msg_type = CHANNEL_TYPE_MAP.get(channel, "SMS")
        body = {"type": msg_type, "contactId": contact_id, "message": message}
        return self._post("/conversations/messages", body)

    def create_opportunity(self, contact_id: str, pipeline_id: str, stage_id: str, name: str) -> dict:
        body = {
            "pipelineId": pipeline_id,
            "locationId": self._location_id,
            "name": name,
            "pipelineStageId": stage_id,
            "status": "open",
            "contactId": contact_id,
        }
        data = self._post("/opportunities/", body)
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

    def search_opportunities(self, contact_id: str) -> list[dict]:
        data = self._get("/opportunities/search", params={"contact_id": contact_id, "location_id": self._location_id})
        return data.get("opportunities", [])
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_ghl.py -v
```

Expected: all 8 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add services/ tests/test_ghl.py
git commit -m "feat: GHL API v2 client with contact, pipeline, messaging, task, workflow methods"
```

---

## Task 4: Google Sheets Client

**Files:**
- Create: `services/sheets.py`
- Create: `tests/test_sheets.py`

The Google Sheet must have these columns (row 1 = headers):
`class_name | start_date | end_date | city | state | price | spots_left | payment_link | calendar_link | active`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_sheets.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create services/sheets.py**

```python
import json
import gspread
from google.oauth2.service_account import Credentials
from models.lead import ClassInfo


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetsClient:
    def __init__(self, service_account_json: str, sheet_id: str):
        creds_dict = json.loads(service_account_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        gc = gspread.authorize(creds)
        self._sheet = gc.open_by_key(sheet_id).sheet1

    def get_active_classes(self) -> list[ClassInfo]:
        rows = self._sheet.get_all_records()
        return [
            ClassInfo(
                name=r["class_name"],
                start_date=r["start_date"],
                end_date=r["end_date"],
                city=r["city"],
                state=r["state"],
                price=str(r["price"]),
                spots_left=int(r["spots_left"]),
                payment_link=r["payment_link"],
                calendar_link=r["calendar_link"],
            )
            for r in rows
            if str(r.get("active", "")).upper() == "TRUE"
        ]

    def get_classes_for_state(self, state: str) -> list[ClassInfo]:
        return [c for c in self.get_active_classes() if c.state.lower() == state.lower()]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_sheets.py -v
```

Expected: all 2 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add services/sheets.py tests/test_sheets.py
git commit -m "feat: Google Sheets client for active classes"
```

---

## Task 5: Engagement Scorer

**Files:**
- Create: `agent/scorer.py`
- Create: `agent/__init__.py`
- Create: `tests/test_scorer.py`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_scorer.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create agent/__init__.py (empty)**

```python
```

- [ ] **Step 4: Create agent/scorer.py**

```python
from models.lead import LeadForm, LeadScore

INVESTMENT_SCORES: dict[str, int] = {
    "I'm ready to commit and start ASAP": 40,
    "Within the next 1-3 months": 25,
    "In 3-6 months, still planning": 10,
    "Just gathering info for now": 5,
}

GOAL_SCORES: dict[str, int] = {
    "Start my own epoxy business and go full-time": 30,
    "Add epoxy services to my existing business": 25,
    "Learn as a hobby or side hustle": 10,
    "Just exploring options right now": 5,
}

EXPERIENCE_SCORES: dict[str, int] = {
    "Yes, I do flooring/construction work now": 10,
    "No, but I'm ready to learn and commit fully": 8,
    "I've done some DIY projects at home": 6,
    "No experience at all, just researching": 3,
}


def score_lead(form: LeadForm, active_states: list[str]) -> LeadScore:
    location_pts = 20 if form.state in active_states else 0
    return LeadScore(
        experience_pts=EXPERIENCE_SCORES.get(form.experience, 0),
        goal_pts=GOAL_SCORES.get(form.goal, 0),
        investment_pts=INVESTMENT_SCORES.get(form.investment, 0),
        location_pts=location_pts,
    )
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_scorer.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add agent/ tests/test_scorer.py
git commit -m "feat: engagement scorer with investment, goal, experience, location weights"
```

---

## Task 6: Conversation Memory

**Files:**
- Create: `agent/memory.py`
- Create: `tests/test_memory.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_memory.py
import os
import pytest
from agent.memory import ConversationStore
from langchain_core.messages import HumanMessage, AIMessage


@pytest.fixture
def store(tmp_path):
    db = str(tmp_path / "test.db")
    s = ConversationStore(db_path=db)
    yield s
    if os.path.exists(db):
        os.remove(db)


def test_empty_history_returns_empty_list(store):
    history = store.get_history("contact_new")
    assert history == []


def test_save_and_load_messages(store):
    store.save_message("contact1", "human", "Hello!")
    store.save_message("contact1", "ai", "Hi there!")
    history = store.get_history("contact1")
    assert len(history) == 2
    assert isinstance(history[0], HumanMessage)
    assert isinstance(history[1], AIMessage)
    assert history[0].content == "Hello!"
    assert history[1].content == "Hi there!"


def test_separate_contacts_have_separate_history(store):
    store.save_message("contact_a", "human", "I'm contact A")
    store.save_message("contact_b", "human", "I'm contact B")
    a_history = store.get_history("contact_a")
    b_history = store.get_history("contact_b")
    assert len(a_history) == 1
    assert len(b_history) == 1
    assert a_history[0].content == "I'm contact A"
    assert b_history[0].content == "I'm contact B"


def test_save_lead_context(store):
    context = {"score": 85, "lead_type": "hot", "state": "Georgia"}
    store.save_context("contact1", context)
    loaded = store.get_context("contact1")
    assert loaded["score"] == 85
    assert loaded["lead_type"] == "hot"


def test_save_opportunity_id(store):
    store.save_opportunity_id("contact1", "opp123")
    assert store.get_opportunity_id("contact1") == "opp123"


def test_get_opportunity_id_returns_none_if_missing(store):
    assert store.get_opportunity_id("contact_new") is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_memory.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create agent/memory.py**

```python
import json
import sqlite3
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage


class ConversationStore:
    def __init__(self, db_path: str = "conversations.db"):
        self._db = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lead_context (
                    contact_id TEXT PRIMARY KEY,
                    context_json TEXT NOT NULL,
                    opportunity_id TEXT
                )
            """)

    def save_message(self, contact_id: str, role: str, content: str):
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "INSERT INTO messages (contact_id, role, content) VALUES (?, ?, ?)",
                (contact_id, role, content),
            )

    def get_history(self, contact_id: str) -> list[BaseMessage]:
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE contact_id = ? ORDER BY id ASC",
                (contact_id,),
            ).fetchall()
        return [
            HumanMessage(content=content) if role == "human" else AIMessage(content=content)
            for role, content in rows
        ]

    def save_context(self, contact_id: str, context: dict):
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                """
                INSERT INTO lead_context (contact_id, context_json)
                VALUES (?, ?)
                ON CONFLICT(contact_id) DO UPDATE SET context_json = excluded.context_json
                """,
                (contact_id, json.dumps(context)),
            )

    def get_context(self, contact_id: str) -> dict:
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT context_json FROM lead_context WHERE contact_id = ?",
                (contact_id,),
            ).fetchone()
        if not row:
            return {}
        return json.loads(row[0])

    def save_opportunity_id(self, contact_id: str, opportunity_id: str):
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                """
                INSERT INTO lead_context (contact_id, context_json, opportunity_id)
                VALUES (?, '{}', ?)
                ON CONFLICT(contact_id) DO UPDATE SET opportunity_id = excluded.opportunity_id
                """,
                (contact_id, opportunity_id),
            )

    def get_opportunity_id(self, contact_id: str) -> str | None:
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT opportunity_id FROM lead_context WHERE contact_id = ?",
                (contact_id,),
            ).fetchone()
        if not row:
            return None
        return row[0]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_memory.py -v
```

Expected: all 6 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/memory.py tests/test_memory.py
git commit -m "feat: SQLite conversation memory with history, context, opportunity tracking"
```

---

## Task 7: Agent Prompts

**Files:**
- Create: `agent/prompts.py`

No tests needed — prompt strings are validated by the agent behavior, not unit tests.

- [ ] **Step 1: Create agent/prompts.py**

```python
from models.lead import LeadType, ClassInfo


def build_system_prompt(lead_type: LeadType, lead_context: dict, classes: list[ClassInfo]) -> str:
    class_info = _format_classes(classes)
    base = f"""You are a friendly, knowledgeable sales agent for JP Resin — a professional epoxy flooring training company.

You are talking to a lead who submitted a form. Here is what you know about them:
- Name: {lead_context.get('first_name', '')} {lead_context.get('last_name', '')}
- State: {lead_context.get('state', '')}
- Experience: {lead_context.get('experience', '')}
- Goal: {lead_context.get('goal', '')}
- Investment timeline: {lead_context.get('investment', '')}
- Engagement score: {lead_context.get('score', 0)}/100
- Lead type: {lead_type.value.upper()}

Available upcoming classes:
{class_info}

RULES:
- Always use their first name.
- Always mention scarcity when relevant (limited spots, upcoming date).
- Never mention the engagement score or lead classification to the lead.
- Keep messages SHORT — this is SMS. 2-4 sentences max.
- Use casual, warm English. No corporate speak.
- If they express readiness to buy, offer: (1) jump on a quick call with JP, or (2) lock in their spot with a payment link.
- If they mention money concerns → send ROI workflow.
- If they ask about the class → send class info workflow.
- NEVER make up prices, dates, or spots — always use the data provided above.
"""

    if lead_type == LeadType.HOT:
        base += """
APPROACH: This lead is HOT. Create urgency. Move fast. Offer JP call or payment link quickly.
"""
    elif lead_type == LeadType.MID:
        base += """
APPROACH: This lead is WARM. Understand their blocker — is it timing, money, or doubt? 
Use what you know about their timeline from the form. Don't ask questions they already answered.
"""
    else:
        base += """
APPROACH: This lead is COLD. Be educational and patient. Build interest. 
Don't push for a sale yet. Ask open questions to understand their situation.
"""

    return base


def _format_classes(classes: list[ClassInfo]) -> str:
    if not classes:
        return "No upcoming classes found."
    lines = []
    for c in classes:
        lines.append(
            f"- {c.name} | {c.city}, {c.state} | {c.start_date} to {c.end_date} | {c.price} | {c.spots_left} spots left"
        )
    return "\n".join(lines)


def build_first_message_hot(first_name: str, class_info: ClassInfo | None) -> str:
    if class_info:
        return (
            f"Hey {first_name}! Saw you're ready to go with epoxy flooring 🔥 "
            f"We only have {class_info.spots_left} spots left for our bootcamp in "
            f"{class_info.city}, {class_info.state} — {class_info.start_date}. "
            f"Would you like to jump on a quick call with JP personally, or are you ready to lock in your spot right now?"
        )
    return (
        f"Hey {first_name}! Saw you're ready to go with epoxy flooring 🔥 "
        f"JP personally teaches every student and spots fill fast. "
        f"Want to jump on a quick call with JP, or are you ready to lock in right now?"
    )


def build_first_message_mid(first_name: str, investment_timeline: str) -> str:
    timeline_messages = {
        "Within the next 1-3 months": (
            f"Hey {first_name}! You mentioned you're aiming to start within the next few months — "
            f"what's the one thing that needs to fall into place for you to pull the trigger?"
        ),
        "In 3-6 months, still planning": (
            f"Hey {first_name}! You're planning for later this year — "
            f"is it more about timing, the investment, or just wanting to learn more first?"
        ),
        "Just gathering info for now": (
            f"Hey {first_name}! No rush at all — "
            f"what's the biggest question you have about epoxy flooring as a business?"
        ),
    }
    return timeline_messages.get(
        investment_timeline,
        f"Hey {first_name}! Thanks for checking out JP Resin. What's your biggest question about getting started?",
    )


def build_first_message_cold(first_name: str) -> str:
    return (
        f"Hey {first_name}! Thanks for your interest in epoxy flooring. "
        f"What's the biggest question you have about getting started as a pro?"
    )
```

- [ ] **Step 2: Verify import works**

```bash
python -c "from agent.prompts import build_first_message_hot, build_first_message_mid, build_first_message_cold; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add agent/prompts.py
git commit -m "feat: agent prompts and first message builders per lead type"
```

---

## Task 8: LangChain Tools

**Files:**
- Create: `agent/tools.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_tools.py
from unittest.mock import MagicMock, patch
from agent.tools import build_tools


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


def test_build_tools_returns_list(monkeypatch):
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


def test_move_pipeline_calls_ghl(monkeypatch):
    ghl, sheets, store, settings = _make_deps()
    ghl.search_opportunities.return_value = [{"id": "opp1"}]
    tools = build_tools(contact_id="c1", ghl=ghl, sheets=sheets, store=store, settings=settings)
    move = next(t for t in tools if t.name == "move_pipeline")
    move.invoke({"stage": "hot"})
    ghl.update_opportunity_stage.assert_called_once_with("opp1", "stage_hot")


def test_send_message_calls_ghl(monkeypatch):
    ghl, sheets, store, settings = _make_deps()
    tools = build_tools(contact_id="c1", ghl=ghl, sheets=sheets, store=store, settings=settings)
    send = next(t for t in tools if t.name == "send_message")
    send.invoke({"message": "Hello!", "channel": "SMS"})
    ghl.send_message.assert_called_once_with(contact_id="c1", message="Hello!", channel="SMS")


def test_get_classes_returns_formatted_string(monkeypatch):
    from models.lead import ClassInfo
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_tools.py -v
```

Expected: `ModuleNotFoundError`.

- [ ] **Step 3: Create agent/tools.py**

```python
from langchain_core.tools import tool
from services.ghl import GHLClient
from services.sheets import SheetsClient
from agent.memory import ConversationStore


STAGE_MAP = {
    "new": "GHL_STAGE_NEW_LEAD",
    "hot": "GHL_STAGE_HOT",
    "mid": "GHL_STAGE_MID",
    "cold": "GHL_STAGE_COLD",
    "in_conversation": "GHL_STAGE_IN_CONVERSATION",
    "call_scheduled": "GHL_STAGE_CALL_SCHEDULED",
    "enrolled": "GHL_STAGE_ENROLLED",
    "not_interested": "GHL_STAGE_NOT_INTERESTED",
}

WORKFLOW_MAP = {
    "nurture_roi": "GHL_WORKFLOW_NURTURE_ROI",
    "nurture_class_info": "GHL_WORKFLOW_NURTURE_CLASS_INFO",
    "followup_hot": "GHL_WORKFLOW_FOLLOWUP_HOT",
    "followup_mid": "GHL_WORKFLOW_FOLLOWUP_MID",
    "followup_cold": "GHL_WORKFLOW_FOLLOWUP_COLD",
}


def build_tools(contact_id: str, ghl: GHLClient, sheets: SheetsClient, store: ConversationStore, settings) -> list:

    @tool
    def move_pipeline(stage: str) -> str:
        """Move the contact to a pipeline stage. Valid stages: new, hot, mid, cold, in_conversation, call_scheduled, enrolled, not_interested."""
        stage_attr = STAGE_MAP.get(stage.lower())
        if not stage_attr:
            return f"Unknown stage: {stage}"
        stage_id = getattr(settings, stage_attr, "")
        if not stage_id:
            return f"Stage ID not configured for: {stage}"
        opps = ghl.search_opportunities(contact_id)
        if opps:
            opp_id = opps[0]["id"]
            ghl.update_opportunity_stage(opp_id, stage_id)
        else:
            context = store.get_context(contact_id)
            name = f"{context.get('first_name', '')} {context.get('last_name', '')}".strip()
            opp = ghl.create_opportunity(contact_id, settings.GHL_PIPELINE_ID, stage_id, name or contact_id)
            store.save_opportunity_id(contact_id, opp["id"])
        return f"Moved to stage: {stage}"

    @tool
    def send_message(message: str, channel: str = "SMS") -> str:
        """Send a message to the lead. channel can be: SMS, Instagram, Facebook."""
        ghl.send_message(contact_id=contact_id, message=message, channel=channel)
        store.save_message(contact_id, "ai", message)
        return f"Message sent via {channel}"

    @tool
    def get_classes() -> str:
        """Get all active upcoming classes with dates, city, state, spots left, and links."""
        classes = sheets.get_active_classes()
        if not classes:
            return "No active classes found."
        lines = [
            f"- {c.name} | {c.city}, {c.state} | {c.start_date}–{c.end_date} | {c.price} | {c.spots_left} spots left | pay: {c.payment_link} | call: {c.calendar_link}"
            for c in classes
        ]
        return "\n".join(lines)

    @tool
    def notify_jp(reason: str) -> str:
        """Create an urgent task in GHL assigned to JP to personally contact this lead."""
        context = store.get_context(contact_id)
        name = f"{context.get('first_name', '')} {context.get('last_name', '')}".strip()
        title = f"🔥 HOT LEAD — Call {name} NOW. Reason: {reason}"
        ghl.create_task(contact_id=contact_id, title=title)
        return "JP notified with urgent task."

    @tool
    def send_payment_link(payment_link: str) -> str:
        """Send the payment link to the lead so they can enroll directly."""
        message = f"Here's your link to lock in your spot: {payment_link} 🔒 Only a few spots left — grab yours now!"
        ghl.send_message(contact_id=contact_id, message=message, channel="SMS")
        store.save_message(contact_id, "ai", message)
        return "Payment link sent."

    @tool
    def send_calendar_link(calendar_link: str) -> str:
        """Send JP's calendar link so the lead can book a call with JP."""
        message = f"Awesome! Here's JP's calendar to book your call: {calendar_link} 📅 Pick a time that works for you!"
        ghl.send_message(contact_id=contact_id, message=message, channel="SMS")
        store.save_message(contact_id, "ai", message)
        return "Calendar link sent."

    @tool
    def trigger_workflow(workflow_name: str) -> str:
        """Trigger a GHL nurture or follow-up workflow. Valid names: nurture_roi, nurture_class_info, followup_hot, followup_mid, followup_cold."""
        wf_attr = WORKFLOW_MAP.get(workflow_name.lower())
        if not wf_attr:
            return f"Unknown workflow: {workflow_name}"
        workflow_id = getattr(settings, wf_attr, "")
        if not workflow_id:
            return f"Workflow ID not configured for: {workflow_name}"
        ghl.trigger_workflow(contact_id=contact_id, workflow_id=workflow_id)
        return f"Workflow triggered: {workflow_name}"

    return [move_pipeline, send_message, get_classes, notify_jp, send_payment_link, send_calendar_link, trigger_workflow]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_tools.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: LangChain tools for pipeline, messaging, classes, notifications, workflows"
```

---

## Task 9: LangChain Agent

**Files:**
- Create: `agent/agent.py`

- [ ] **Step 1: Create agent/agent.py**

```python
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from config import settings
from models.lead import LeadType, ClassInfo
from services.ghl import GHLClient
from services.sheets import SheetsClient
from agent.memory import ConversationStore
from agent.tools import build_tools
from agent.prompts import build_system_prompt


def create_agent(
    contact_id: str,
    lead_type: LeadType,
    lead_context: dict,
    classes: list[ClassInfo],
    ghl: GHLClient,
    sheets: SheetsClient,
    store: ConversationStore,
) -> AgentExecutor:
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_base="https://api.deepseek.com/v1",
        openai_api_key=settings.DEEPSEEK_API_KEY,
        temperature=0.7,
    )

    tools = build_tools(
        contact_id=contact_id,
        ghl=ghl,
        sheets=sheets,
        store=store,
        settings=settings,
    )

    system_prompt = build_system_prompt(lead_type, lead_context, classes)
    history = store.get_history(contact_id)

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
    ), history


def run_agent(
    contact_id: str,
    human_message: str,
    lead_type: LeadType,
    lead_context: dict,
    classes: list[ClassInfo],
    ghl: GHLClient,
    sheets: SheetsClient,
    store: ConversationStore,
) -> str:
    executor, history = create_agent(
        contact_id=contact_id,
        lead_type=lead_type,
        lead_context=lead_context,
        classes=classes,
        ghl=ghl,
        sheets=sheets,
        store=store,
    )
    store.save_message(contact_id, "human", human_message)
    result = executor.invoke({
        "input": human_message,
        "chat_history": history,
    })
    output = result["output"]
    store.save_message(contact_id, "ai", output)
    return output
```

- [ ] **Step 2: Verify import**

```bash
python -c "from agent.agent import run_agent; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add agent/agent.py
git commit -m "feat: LangChain AgentExecutor with DeepSeek, tools, and conversation memory"
```

---

## Task 10: FastAPI Webhooks

**Files:**
- Modify: `main.py`
- Create: `tests/test_webhooks.py`

- [ ] **Step 1: Write failing tests**

```python
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

    from main import app
    client = TestClient(app)
    resp = client.post(
        "/webhook/new-lead",
        json=_new_lead_payload(),
        headers={"x-webhook-secret": "changeme"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "processed"


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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_webhooks.py -v
```

Expected: health passes, webhook tests fail (not implemented yet).

- [ ] **Step 3: Implement main.py**

```python
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel
from typing import Optional

from config import settings
from models.lead import LeadForm, LeadType
from services.ghl import GHLClient
from services.sheets import SheetsClient
from agent.scorer import score_lead
from agent.memory import ConversationStore
from agent.agent import run_agent
from agent.prompts import build_first_message_hot, build_first_message_mid, build_first_message_cold


app = FastAPI(title="JP Resin Precalificador")


def _get_deps():
    ghl = GHLClient(pit_token=settings.GHL_PIT_TOKEN, location_id=settings.GHL_LOCATION_ID)
    sheets = SheetsClient(
        service_account_json=settings.GOOGLE_SERVICE_ACCOUNT_JSON,
        sheet_id=settings.GOOGLE_SHEETS_ID,
    )
    store = ConversationStore(db_path=settings.DB_PATH)
    return ghl, sheets, store


def _verify_secret(secret: Optional[str]):
    if secret != settings.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhook/new-lead")
async def new_lead(request: Request, x_webhook_secret: Optional[str] = Header(None)):
    _verify_secret(x_webhook_secret)
    body = await request.json()

    contact = body.get("contact", body)
    contact_id = contact.get("id", "")
    first_name = contact.get("firstName", "")
    last_name = contact.get("lastName", "")
    email = contact.get("email", "")
    phone = contact.get("phone", "")
    state = contact.get("state", "")

    custom_fields = {f["id"]: f["value"] for f in contact.get("customFields", [])}
    experience = custom_fields.get(settings.GHL_FIELD_EXPERIENCE, "")
    goal = custom_fields.get(settings.GHL_FIELD_GOAL, "")
    investment = custom_fields.get(settings.GHL_FIELD_INVESTMENT, "")

    form = LeadForm(
        contact_id=contact_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        state=state,
        experience=experience,
        goal=goal,
        investment=investment,
        channel="SMS",
    )

    ghl, sheets, store = _get_deps()
    classes = sheets.get_active_classes()
    active_states = list({c.state for c in classes})
    lead_score = score_lead(form, active_states)

    lead_context = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "state": state,
        "experience": experience,
        "goal": goal,
        "investment": investment,
        "score": lead_score.total,
        "lead_type": lead_score.lead_type.value,
    }
    store.save_context(contact_id, lead_context)

    stage = lead_score.lead_type.value
    opps = ghl.search_opportunities(contact_id)
    if opps:
        stage_attr = f"GHL_STAGE_{stage.upper()}"
        stage_id = getattr(settings, stage_attr, "")
        if stage_id:
            ghl.update_opportunity_stage(opps[0]["id"], stage_id)
    else:
        stage_attr = f"GHL_STAGE_{stage.upper()}"
        stage_id = getattr(settings, stage_attr, "")
        if stage_id:
            opp = ghl.create_opportunity(contact_id, settings.GHL_PIPELINE_ID, stage_id, f"{first_name} {last_name}")
            store.save_opportunity_id(contact_id, opp["id"])

    state_classes = [c for c in classes if c.state.lower() == state.lower()]
    first_class = state_classes[0] if state_classes else (classes[0] if classes else None)

    if lead_score.lead_type == LeadType.HOT:
        first_message = build_first_message_hot(first_name, first_class)
    elif lead_score.lead_type == LeadType.MID:
        first_message = build_first_message_mid(first_name, investment)
    else:
        first_message = build_first_message_cold(first_name)

    ghl.send_message(contact_id=contact_id, message=first_message, channel="SMS")
    store.save_message(contact_id, "ai", first_message)

    return {"status": "processed", "score": lead_score.total, "lead_type": lead_score.lead_type.value}


class ReplyPayload(BaseModel):
    contactId: str
    message: str
    channel: str = "SMS"


@app.post("/webhook/reply")
async def reply(payload: ReplyPayload, x_webhook_secret: Optional[str] = Header(None)):
    _verify_secret(x_webhook_secret)

    ghl, sheets, store = _get_deps()
    lead_context = store.get_context(payload.contactId)

    if not lead_context:
        raise HTTPException(status_code=404, detail="Contact context not found")

    lead_type = LeadType(lead_context.get("lead_type", "cold"))
    classes = sheets.get_active_classes()

    response = run_agent(
        contact_id=payload.contactId,
        human_message=payload.message,
        lead_type=lead_type,
        lead_context=lead_context,
        classes=classes,
        ghl=ghl,
        sheets=sheets,
        store=store,
    )

    return {"status": "ok", "response": response}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_webhooks.py -v
```

Expected: all 4 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_webhooks.py
git commit -m "feat: FastAPI webhooks for new leads and replies with scoring, pipeline, and first message"
```

---

## Task 11: GHL Setup Script

**Files:**
- Create: `scripts/fetch_ghl_ids.py`

This one-time script fetches all IDs you need to fill in `.env`. Run it once after deploy.

- [ ] **Step 1: Create scripts/fetch_ghl_ids.py**

```python
"""
Run this once to fetch your GHL pipeline stage IDs and custom field IDs.
Usage: python scripts/fetch_ghl_ids.py
Copy the output into your .env file.
"""
import os
import sys
import json
import httpx

PIT_TOKEN = os.getenv("GHL_PIT_TOKEN", "pit-434e3525-02b4-4960-a9e2-fc3f58d4d0fb")
LOCATION_ID = os.getenv("GHL_LOCATION_ID", "AWQqYSyxdYeqqhoLc0ef")
BASE = "https://services.leadconnectorhq.com"
HEADERS = {"Authorization": f"Bearer {PIT_TOKEN}", "Version": "2021-07-28"}


def get(path, params=None):
    resp = httpx.get(f"{BASE}{path}", headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()


def main():
    print("\n=== PIPELINES & STAGES ===\n")
    data = get("/opportunities/pipelines", params={"locationId": LOCATION_ID})
    for pipeline in data.get("pipelines", []):
        print(f"Pipeline: {pipeline['name']} | ID: {pipeline['id']}")
        print(f"  GHL_PIPELINE_ID={pipeline['id']}")
        for stage in pipeline.get("stages", []):
            print(f"  Stage: {stage['name']} | ID: {stage['id']}")

    print("\n=== CUSTOM FIELDS ===\n")
    data = get(f"/locations/{LOCATION_ID}/customFields")
    for field in data.get("customFields", []):
        print(f"Field: {field['name']} | ID: {field['id']}")

    print("\n=== WORKFLOWS ===\n")
    try:
        data = get(f"/workflows/", params={"locationId": LOCATION_ID})
        for wf in data.get("workflows", []):
            print(f"Workflow: {wf['name']} | ID: {wf['id']}")
    except Exception as e:
        print(f"Could not fetch workflows: {e}")

    print("\nCopy the IDs above into your .env file.\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script (requires valid credentials)**

```bash
python scripts/fetch_ghl_ids.py
```

Expected: prints all pipeline stages, custom fields, and workflows with their IDs.

- [ ] **Step 3: Fill in .env with the IDs from the output**

Copy each ID to the corresponding variable in `.env`:
```
GHL_PIPELINE_ID=<from output>
GHL_STAGE_HOT=<stage ID for Hot Lead>
GHL_STAGE_MID=<stage ID for Mid Lead>
GHL_STAGE_COLD=<stage ID for Cold Lead>
GHL_STAGE_IN_CONVERSATION=<stage ID for In Conversation>
GHL_STAGE_CALL_SCHEDULED=<stage ID for Call Scheduled>
GHL_STAGE_ENROLLED=<stage ID for Enrolled>
GHL_STAGE_NOT_INTERESTED=<stage ID for Not Interested>
GHL_FIELD_EXPERIENCE=<field ID for epoxy experience question>
GHL_FIELD_GOAL=<field ID for main goal question>
GHL_FIELD_INVESTMENT=<field ID for investment timeline question>
```

- [ ] **Step 4: Commit**

```bash
git add scripts/fetch_ghl_ids.py
git commit -m "feat: setup script to fetch GHL pipeline, field, and workflow IDs"
```

---

## Task 12: Full Test Suite + Render Deploy

**Files:**
- Create: `tests/conftest.py`

- [ ] **Step 1: Create tests/conftest.py**

pydantic-settings reads env vars when `Settings()` is first instantiated at import time, so we must set `os.environ` at module level — before any test module imports `config`.

```python
import os

# Must be set before any import of config.py (pydantic-settings reads at instantiation)
os.environ.setdefault("GHL_PIT_TOKEN", "test-token")
os.environ.setdefault("GHL_LOCATION_ID", "loc123")
os.environ.setdefault("DEEPSEEK_API_KEY", "test-key")
os.environ.setdefault("GOOGLE_SHEETS_ID", "sheet123")
os.environ.setdefault("GOOGLE_SERVICE_ACCOUNT_JSON", '{"type":"service_account","project_id":"test","private_key_id":"x","private_key":"x","client_email":"x@x.iam.gserviceaccount.com","client_id":"1","auth_uri":"https://x","token_uri":"https://x"}')
os.environ.setdefault("WEBHOOK_SECRET", "changeme")
os.environ.setdefault("DB_PATH", ":memory:")
```

- [ ] **Step 2: Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: all tests PASS (at minimum: test_models, test_scorer, test_memory, test_ghl, test_sheets, test_tools, test_webhooks).

- [ ] **Step 3: Verify server starts**

```bash
cp .env.example .env
# Fill in real credentials
uvicorn main:app --reload
curl http://localhost:8000/health
```

Expected: `{"status": "ok"}`

- [ ] **Step 4: Deploy to Render**

1. Push repo to GitHub
2. On Render dashboard: New → Web Service → connect repo
3. Add all `.env` variables in Render's Environment tab
4. Deploy — Render uses `render.yaml` automatically

- [ ] **Step 5: Configure GHL Webhook**

In GHL subcuenta JP Resin:
1. Settings → Integrations → Webhooks
2. Add webhook: `https://your-render-url.onrender.com/webhook/new-lead`
   - Event: `Contact Created`
   - Header: `x-webhook-secret: <your WEBHOOK_SECRET>`
3. Add second webhook: `https://your-render-url.onrender.com/webhook/reply`
   - Event: `Inbound Message`
   - Header: `x-webhook-secret: <your WEBHOOK_SECRET>`

- [ ] **Step 6: Final commit**

```bash
git add tests/conftest.py
git commit -m "feat: test conftest, full suite verified, ready for Render deploy"
```

---

## Pipeline Stages to Create in GHL

Before running the setup script, manually create these stages in your GHL pipeline (Opportunities → Pipelines → Create/Edit):

| Stage Name | Purpose |
|---|---|
| New Lead | Auto-entry point |
| Hot Lead | Score 70-100 |
| Mid Lead | Score 40-69 |
| Cold Lead | Score 0-39 |
| In Conversation | Agent actively talking |
| Call Scheduled | Booked call with JP |
| Enrolled | Paid and registered |
| Not Interested | Closed |

## Google Sheet Format

Ensure your sheet at `1p0avMlP5xFm1nWj2CkYD0ream60Ot4ed7qdzdvskqmI` has row 1 as headers:

```
class_name | start_date | end_date | city | state | price | spots_left | payment_link | calendar_link | active
```

Example row:
```
4-Day Epoxy Bootcamp | 2026-04-27 | 2026-04-30 | Atlanta | Georgia | $2,500 | 5 | https://pay.link | https://cal.link | TRUE
```
