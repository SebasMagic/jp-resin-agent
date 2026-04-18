import hmac
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
    sheets = SheetsClient(csv_url=settings.GOOGLE_SHEETS_CSV_URL)
    store = ConversationStore(db_path=settings.DB_PATH)
    return ghl, sheets, store


def _verify_secret(secret: str | None):
    if not secret or not hmac.compare_digest(secret, settings.WEBHOOK_SECRET):
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
    if not contact_id:
        raise HTTPException(status_code=422, detail="Missing contact id in payload")
    first_name = contact.get("firstName", "")
    last_name = contact.get("lastName", "")
    email = contact.get("email", "")
    phone = contact.get("phone", "")
    state = contact.get("state", "")

    # Tag filter — if TEST_TAG is configured, skip contacts without it
    if settings.TEST_TAG:
        tags = contact.get("tags", [])
        if settings.TEST_TAG not in tags:
            return {"status": "skipped", "reason": f"contact missing tag '{settings.TEST_TAG}'"}

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
    stage_attr = f"GHL_STAGE_{stage.upper()}"
    stage_id = getattr(settings, stage_attr, "")
    opps = ghl.search_opportunities(contact_id, pipeline_id=settings.GHL_PIPELINE_ID)
    if opps:
        if stage_id:
            ghl.update_opportunity_stage(opps[0]["id"], stage_id)
    else:
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

    try:
        ghl.send_message(contact_id=contact_id, message=first_message, channel="SMS")
        store.save_message(contact_id, "ai", first_message)
    except Exception:
        pass  # lead is scored and in pipeline; don't fail webhook on messaging error

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

    try:
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
    except Exception as exc:
        return {"status": "error", "response": f"Agent temporarily unavailable: {exc}"}

    return {"status": "ok", "response": response}
