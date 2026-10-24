from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Language = Literal['auto', 'en', 'hi', 'hinglish']
Care = Literal['paramedic_home_visit', 'nurse_home_visit', 'gp_teleconsult',
               'specialist_consult', 'emergency_referral']
Urgency = Literal['routine', 'same_day', 'immediate']


class Location(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class Message(BaseModel):
    role: Literal['user', 'assistant']
    content: str = Field(min_length=1, max_length=2000)


class AssessmentRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    user_input: str = Field(min_length=1, max_length=2000)
    language: Language = 'auto'
    location: Location | None = None
    conversation_history: list[Message] = Field(default_factory=list, max_length=16)


class Match(BaseModel):
    caregiver_id: str
    score: float = Field(ge=0, le=1)
    reason: str


class AssessmentResponse(BaseModel):
    follow_up_question: str | None = None
    care_type: Care | None = None
    urgency: Urgency | None = None
    red_flags: list[str] = Field(default_factory=list)
    reasoning: str
    matched_caregivers: list[Match] = Field(default_factory=list)


class Turn(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    user_input: str = Field(min_length=1, max_length=2000)
    expected_version: int = Field(ge=0)
    question_id: str | None = Field(default=None, max_length=30)
    language: Language = 'en'
    location: Location | None = None


class BookingRequest(BaseModel):
    session_id: str = Field(min_length=10, max_length=100)
    decision_version: int = Field(ge=1)
    caregiver_id: str = Field(min_length=1, max_length=50)
    slot_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=8, max_length=100)
