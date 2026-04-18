from enum import Enum
from pydantic import BaseModel, ConfigDict, computed_field


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
    model_config = ConfigDict(use_enum_values=True)

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
