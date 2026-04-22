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


def build_tools(contact_id: str, ghl: GHLClient, sheets: SheetsClient, store: ConversationStore, settings, lead_channel: str = "SMS") -> list:

    def _get_or_create_opportunity(stage_id: str) -> str:
        opps = ghl.search_opportunities(contact_id, pipeline_id=settings.GHL_PIPELINE_ID)
        if not opps:
            opps = ghl.get_opportunities_by_contact(contact_id)
        if opps:
            opp_id = opps[0]["id"]
            ghl.update_opportunity_stage(opp_id, stage_id)
            store.save_opportunity_id(contact_id, opp_id)
            return opp_id
        context = store.get_context(contact_id)
        name = f"{context.get('first_name', '')} {context.get('last_name', '')}".strip()
        try:
            opp = ghl.create_opportunity(contact_id, settings.GHL_PIPELINE_ID, stage_id, name or contact_id)
            store.save_opportunity_id(contact_id, opp["id"])
            return opp["id"]
        except Exception:
            opps = ghl.get_opportunities_by_contact(contact_id)
            if opps:
                store.save_opportunity_id(contact_id, opps[0]["id"])
                ghl.update_opportunity_stage(opps[0]["id"], stage_id)
                return opps[0]["id"]
            raise

    @tool
    def move_pipeline(stage: str) -> str:
        """Move the contact to a pipeline stage. Valid stages: new, hot, mid, cold, in_conversation, call_scheduled, enrolled, not_interested."""
        stage_attr = STAGE_MAP.get(stage.lower())
        if not stage_attr:
            return f"Unknown stage: {stage}"
        stage_id = getattr(settings, stage_attr, "")
        if not stage_id:
            return f"Stage ID not configured for: {stage}"
        _get_or_create_opportunity(stage_id)
        return f"Moved to stage: {stage}"

    @tool
    def get_classes() -> str:
        """Get all active upcoming classes with dates, city, state, price, spots left, and links."""
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
        """Create an urgent GHL task to notify JP to contact this lead personally."""
        context = store.get_context(contact_id)
        name = f"{context.get('first_name', '')} {context.get('last_name', '')}".strip()
        title = f"🔥 HOT LEAD — Call {name} NOW. Reason: {reason}"
        ghl.create_task(contact_id=contact_id, title=title)
        return "JP notified with urgent task."

    @tool
    def send_payment_link(payment_link: str, channel: str = "") -> str:
        """Send the payment link to the lead. Pass the exact payment_link from get_classes. channel: SMS, Instagram, or Facebook. Leave empty to use the lead's channel."""
        message = f"Here's your link to lock in your spot: {payment_link} 🔒 Only a few spots left — grab yours now!"
        ghl.send_message(contact_id=contact_id, message=message, channel=channel or lead_channel)
        store.save_message(contact_id, "ai", message)
        return "Payment link sent."

    @tool
    def send_calendar_link(calendar_link: str, channel: str = "") -> str:
        """Send JP's calendar link to book a call. Pass the exact calendar_link from get_classes. channel: SMS, Instagram, or Facebook. Leave empty to use the lead's channel."""
        message = f"Awesome! Here's JP's calendar to book your call: {calendar_link} 📅 Pick a time that works for you!"
        ghl.send_message(contact_id=contact_id, message=message, channel=channel or lead_channel)
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

    return [move_pipeline, get_classes, notify_jp, send_payment_link, send_calendar_link, trigger_workflow]
