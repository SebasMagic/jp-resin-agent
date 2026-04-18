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
