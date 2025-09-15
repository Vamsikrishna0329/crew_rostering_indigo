
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
class GenerateRosterRequest(BaseModel):
    period_start: date
    period_end: date
    rules_version: str = "v1"
    optimization_method: str = "simple"  # Can be "simple" or "or_tools"
class DutyAssignment(BaseModel):
    crew_id: Optional[int]
    crew_name: Optional[str]  # Add crew name for better display
    flight_id: int
    duty_start_utc: datetime
    duty_end_utc: datetime
    note: Optional[str] = None
class RosterResponse(BaseModel):
    status: str = "Draft"
    period_start: date
    period_end: date
    assignments: List[DutyAssignment] = Field(default_factory=list)
    kpis: dict = Field(default_factory=dict)
class ReRosteringRequest(BaseModel):
    flight_no: str
    type: str
    delay_minutes: int = 0
    crew_id: Optional[int] = None
    unavailable_from: Optional[date] = None
    unavailable_to: Optional[date] = None
    reason: Optional[str] = None
class PatchResponse(BaseModel):
    status: str
    patch: dict
    kpis: dict
