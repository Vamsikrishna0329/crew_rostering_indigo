
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date, datetime
from app.storage.db import SessionLocal
from app.schemas.roster import GenerateRosterRequest, RosterResponse
from app.services.orchestrator import run_generate_roster
from app.storage import models
from typing import List, Dict, Any, Optional

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/generate", response_model=RosterResponse)
def generate_roster(req: GenerateRosterRequest, db: Session = Depends(get_db)):
    assignments, kpis = run_generate_roster(db, req.period_start, req.period_end, req.rules_version, req.optimization_method)
    return RosterResponse(status="Draft", period_start=req.period_start, period_end=req.period_end, assignments=assignments, kpis=kpis)

@router.get("/calendar")
def get_roster_calendar(
    db: Session = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
    crew_id: Optional[int] = Query(None)
):
    """Get roster data formatted for calendar/timeline view"""
    try:
        # Query duty periods with flight details
        query = db.query(
            models.DutyPeriod,
            models.Flight,
            models.Crew
        ).join(
            models.DutyFlight, models.DutyPeriod.duty_id == models.DutyFlight.duty_id
        ).join(
            models.Flight, models.DutyFlight.flight_id == models.Flight.flight_id
        ).join(
            models.Crew, models.DutyPeriod.crew_id == models.Crew.crew_id
        ).filter(
            models.DutyPeriod.duty_start_utc >= start_date,
            models.DutyPeriod.duty_end_utc <= end_date
        )
        
        if crew_id:
            query = query.filter(models.DutyPeriod.crew_id == crew_id)
        
        results = query.all()
        
        # Format data for calendar view
        calendar_events = []
        for duty, flight, crew in results:
            # Determine role for color coding
            role = crew.rank
            color = "#3b82f6"  # Blue for Captain
            if role == "FirstOfficer":
                color = "#10b981"  # Green for First Officer
            elif role == "FlightAttendant":
                color = "#8b5cf6"  # Purple for Flight Attendant
                
            calendar_events.append({
                "id": f"{duty.duty_id}-{flight.flight_id}",
                "title": f"{flight.flight_no} ({crew.name})",
                "start": duty.duty_start_utc.isoformat(),
                "end": duty.duty_end_utc.isoformat(),
                "resourceId": crew.crew_id,
                "crew_id": crew.crew_id,
                "crew_name": crew.name,
                "crew_role": role,
                "flight_id": flight.flight_id,
                "flight_no": flight.flight_no,
                "dep_iata": flight.dep_iata,
                "arr_iata": flight.arr_iata,
                "color": color,
                "status": "assigned"  # This would be determined by actual status
            })
        
        return {"events": calendar_events}
    except Exception as e:
        # Log the error and return empty events
        print(f"Error in calendar endpoint: {str(e)}")
        return {"events": []}

@router.get("/crew-gantt")
def get_crew_gantt_view(
    db: Session = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
    crew_ids: List[int] = Query(None)
):
    """Get roster data formatted for crew-centric Gantt view"""
    try:
        # Query duty periods with flight details
        query = db.query(
            models.DutyPeriod,
            models.Flight,
            models.Crew
        ).join(
            models.DutyFlight, models.DutyPeriod.duty_id == models.DutyFlight.duty_id
        ).join(
            models.Flight, models.DutyFlight.flight_id == models.Flight.flight_id
        ).join(
            models.Crew, models.DutyPeriod.crew_id == models.Crew.crew_id
        ).filter(
            models.DutyPeriod.duty_start_utc >= start_date,
            models.DutyPeriod.duty_end_utc <= end_date
        )
        
        if crew_ids:
            query = query.filter(models.DutyPeriod.crew_id.in_(crew_ids))
        
        results = query.all()
        
        # Group by crew for Gantt view
        crew_data = {}
        for duty, flight, crew in results:
            if crew.crew_id not in crew_data:
                crew_data[crew.crew_id] = {
                    "crew_id": crew.crew_id,
                    "crew_name": crew.name,
                    "crew_role": crew.rank,
                    "base_iata": crew.base_iata,
                    "duties": []
                }
            
            crew_data[crew.crew_id]["duties"].append({
                "id": f"{duty.duty_id}-{flight.flight_id}",
                "flight_no": flight.flight_no,
                "start": duty.duty_start_utc.isoformat(),
                "end": duty.duty_end_utc.isoformat(),
                "dep_iata": flight.dep_iata,
                "arr_iata": flight.arr_iata,
                "aircraft_code": flight.aircraft_code
            })
        
        return {"crew_data": list(crew_data.values())}
    except Exception as e:
        # Log the error and return empty data
        print(f"Error in Gantt endpoint: {str(e)}")
        return {"crew_data": []}

@router.get("/conflicts")
def get_roster_conflicts(
    db: Session = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
    severity: Optional[str] = Query(None),
    conflict_type: Optional[str] = Query(None)
):
    """Get conflicts and violations in the roster"""
    try:
        from app.optimizer.conflict_detector import detect_conflicts, filter_conflicts
        
        # Detect actual conflicts using the conflict detector
        conflicts = detect_conflicts(db, start_date, end_date)
        
        # Filter conflicts if requested
        if severity or conflict_type:
            conflicts = filter_conflicts(conflicts, severity, conflict_type)
        
        # Add IDs to conflicts for frontend display
        for i, conflict in enumerate(conflicts):
            conflict["id"] = i + 1
        
        return {"conflicts": conflicts}
    except Exception as e:
        # Log the error and return empty conflicts
        print(f"Error in conflicts endpoint: {str(e)}")
        return {"conflicts": []}

@router.get("/disruptions")
def get_disruptions(
    db: Session = Depends(get_db),
    start_date: date = Query(...),
    end_date: date = Query(...),
    disruption_type: Optional[str] = Query(None)
):
    """Get disruptions feed"""
    # Query disruption records
    query = db.query(models.DisruptionRecord).filter(
        models.DisruptionRecord.disruption_date >= start_date,
        models.DisruptionRecord.disruption_date <= end_date
    )
    
    if disruption_type:
        query = query.filter(models.DisruptionRecord.disruption_type == disruption_type)
    
    disruptions = query.order_by(models.DisruptionRecord.disruption_date.desc()).all()
    
    disruption_list = []
    for d in disruptions:
        disruption_list.append({
            "id": d.disruption_id,
            "type": d.disruption_type,
            "flight_no": d.flight_no,
            "crew_id": d.crew_id,
            "date": d.disruption_date.isoformat(),
            "impact_duration": d.impact_duration,
            "reason": d.reason,
            "resolution": d.resolution,
            "recorded_at": d.recorded_at.isoformat() if d.recorded_at else None
        })
    
    return {"disruptions": disruption_list}

@router.get("/rules/classification")
def get_rule_classification():
    """Get hard/soft rule classification"""
    from app.rules.hard_soft_engine import HardSoftRulesEngine
    rules = HardSoftRulesEngine()
    classification = rules.get_rule_categories()
    return {"classification": classification}
