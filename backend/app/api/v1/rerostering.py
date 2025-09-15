
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.storage.db import SessionLocal
from app.schemas.roster import ReRosteringRequest, PatchResponse
from app.services.orchestrator import run_reroster_delay, run_handle_cancellation, run_handle_crew_unavailability
from datetime import date

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=PatchResponse)
def reroster(req: ReRosteringRequest, db: Session = Depends(get_db)):
    # Normalize the request type to handle any encoding issues
    req_type = req.type.strip() if req.type else ""
    
    # Convert to lowercase for case-insensitive comparison
    req_type_lower = req_type.lower()
    
    # Handle different disruption types
    if req_type_lower in ["delay", "flight delay", "flight_delay"]:
        patch, kpis = run_reroster_delay(db, req.flight_no, req.delay_minutes, "v1")
        return PatchResponse(status="Proposed" if "error" not in patch else "Error", patch=patch, kpis=kpis)
    elif req_type_lower in ["cancellation", "flight cancellation", "flight_cancellation"]:
        result, kpis = run_handle_cancellation(db, req.flight_no, "v1")
        return PatchResponse(status="Handled" if "error" not in result else "Error", patch=result, kpis=kpis)
    elif req_type_lower in ["crewunavailability", "crew unavailability", "crew_unavailability"]:
        if req.crew_id is None or req.unavailable_from is None or req.unavailable_to is None:
            return PatchResponse(status="Error", patch={"error": "Missing required parameters for crew unavailability"}, kpis={})
        result, kpis = run_handle_crew_unavailability(db, req.crew_id, req.unavailable_from, req.unavailable_to, "v1")
        return PatchResponse(status="Handled" if "error" not in result else "Error", patch=result, kpis=kpis)
    else:
        return PatchResponse(status="Unsupported", patch={"type": req_type, "original": req.type}, kpis={})
