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
- Lead type: {lead_type.value.upper()}

Available upcoming classes:
{class_info}

RULES:
- ALWAYS respond in English. No matter what language the lead writes in, your reply must be in English.
- Always use their first name.
- Always mention scarcity when relevant (limited spots, upcoming date).
- Never mention the engagement score or lead classification to the lead.
- Keep messages SHORT — this is SMS/DM. 2-4 sentences max.
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
            f"- {c.name} | {c.city}, {c.state} | {c.start_date} to {c.end_date} | {c.price} | {c.spots_scarcity} spots left"
        )
    return "\n".join(lines)


def build_first_message_hot(first_name: str, class_info: ClassInfo | None) -> str:
    if class_info:
        return (
            f"Hey {first_name}! 🔥 Only {class_info.spots_scarcity} spots left for JP Resin's bootcamp "
            f"in {class_info.city} — {class_info.start_date}. "
            f"Ready to lock in, or want a quick call with JP first?"
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
