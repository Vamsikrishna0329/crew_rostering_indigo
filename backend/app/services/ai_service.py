
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.storage import models
from app.ai.llm_agent import suggest_patch, ask_freeform
def build_context_for_flight(db: Session, flight_no: str) -> Dict[str, Any]:
    f = db.query(models.Flight).filter(models.Flight.flight_no == flight_no).order_by(models.Flight.flight_date.desc()).first()
    if not f:
        return {"error": "flight_not_found", "flight_no": flight_no}
    
    # Get only qualified crew for this aircraft type, limited to 10
    qualified_crew = db.query(models.Crew).join(
        models.CrewQualification,
        models.Crew.crew_id == models.CrewQualification.crew_id
    ).filter(
        models.Crew.status == "Active",
        models.CrewQualification.aircraft_code == f.aircraft_code
    ).limit(10).all()
    
    crew_pool = [{"crew_id": c.crew_id, "rank": c.rank, "base": c.base_iata} for c in qualified_crew]
    
    # Get crew preferences
    from datetime import date
    today = date.today()
    prefs = db.query(models.CrewPreference).filter(
        models.CrewPreference.crew_id.in_([c.crew_id for c in qualified_crew]),
        (models.CrewPreference.valid_from.is_(None) | (models.CrewPreference.valid_from <= today)),
        (models.CrewPreference.valid_to.is_(None) | (models.CrewPreference.valid_to >= today))
    ).all()
    
    pref_map = {}
    for p in prefs:
        if p.crew_id not in pref_map:
            pref_map[p.crew_id] = []
        pref_map[p.crew_id].append({
            "type": p.preference_type,
            "value": p.preference_value,
            "weight": p.weight
        })
    
    # Add preferences to crew pool
    for crew_info in crew_pool:
        crew_info["preferences"] = pref_map.get(crew_info["crew_id"], [])
    
    return {
        "flight": {
            "flight_id": f.flight_id,
            "flight_no": f.flight_no,
            "date": str(f.flight_date),
            "dep": f.dep_iata,
            "arr": f.arr_iata,
            "sched_dep_utc": str(f.sched_dep_utc),
            "sched_arr_utc": str(f.sched_arr_utc),
            "aircraft_code": f.aircraft_code
        },
        "crew_pool": crew_pool,
        "constraints_note": "Respect DGCA duty/rest/FDP; assign only qualified crew; consider crew preferences and fairness.",
        "optimization_context": {
            "preference_weight": 10,
            "fairness_weight": 5,
            "compliance_weight": 100  # High weight for compliance
        }
    }
def ai_reroster_suggest(db: Session, flight_no: str) -> Dict[str, Any]:
    ctx = build_context_for_flight(db, flight_no)
    if "error" in ctx:
        return ctx
    try:
        return suggest_patch(ctx)
    except RuntimeError as e:
        return {"error": str(e)}

def ai_handle_disruption(db: Session, flight_no: str, disruption_type: str) -> Dict[str, Any]:
    ctx = build_context_for_flight(db, flight_no)
    if "error" in ctx:
        return ctx
    
    # Add disruption context
    ctx["disruption"] = {
        "type": disruption_type,
        "flight_no": flight_no
    }
    
    try:
        return suggest_patch(ctx)
    except RuntimeError as e:
        return {"error": str(e)}

def ai_ask(db: Session, question: str) -> str:
    # Build enhanced context based on question content
    ctx = build_enhanced_context(db, question)
    return ask_freeform(question, ctx)

def ai_capture_feedback(suggestion: Dict[str,Any], feedback: str, rating: int) -> None:
    """
    Capture feedback on AI suggestions to enable learning capabilities.
    """
    from app.ai.llm_agent import capture_feedback
    capture_feedback(suggestion, feedback, rating)

def build_enhanced_context(db: Session, question: str) -> Dict[str, Any]:
    """Build enhanced context for AI by parsing the question and querying relevant data."""
    # Get basic counts and latest flight info
    latest = db.query(models.Flight).order_by(models.Flight.flight_date.desc()).first()
    counts = {
        "crew_active": db.query(models.Crew).filter(models.Crew.status == "Active").count(),
        "flights_total": db.query(models.Flight).count(),
        "aircraft_types": db.query(models.AircraftType).count()
    }
    
    ctx = {
        "counts": counts,
        "latest_flight": getattr(latest, "flight_no", None),
        "enhanced_data": {}
    }
    
    # Convert question to lowercase for easier matching
    q_lower = question.lower()
    
    # Check for specific queries and add relevant data
    if "flight" in q_lower:
        # Add flight-related data
        if "6e" in q_lower or "flight no" in q_lower or "flight number" in q_lower:
            # Try to extract flight number from question
            import re
            flight_match = re.search(r"[6][Ee]\d{4}", question)
            if flight_match:
                flight_no = flight_match.group(0).upper()
                flight = db.query(models.Flight).filter(models.Flight.flight_no == flight_no).first()
                if flight:
                    ctx["enhanced_data"]["flight_details"] = {
                        "flight_no": flight.flight_no,
                        "flight_date": str(flight.flight_date),
                        "dep_iata": flight.dep_iata,
                        "arr_iata": flight.arr_iata,
                        "sched_dep_utc": str(flight.sched_dep_utc),
                        "sched_arr_utc": str(flight.sched_arr_utc),
                        "aircraft_code": flight.aircraft_code
                    }
        else:
            # Get recent flights
            recent_flights = db.query(models.Flight).order_by(models.Flight.flight_date.desc()).limit(5).all()
            ctx["enhanced_data"]["recent_flights"] = [
                {
                    "flight_no": f.flight_no,
                    "flight_date": str(f.flight_date),
                    "dep_iata": f.dep_iata,
                    "arr_iata": f.arr_iata
                }
                for f in recent_flights
            ]
    
    if "crew" in q_lower:
        # Add crew-related data
        if "crew id" in q_lower or "crew_id" in q_lower:
            # Try to extract crew ID from question
            import re
            crew_match = re.search(r"crew\s*(?:id)?\s*(\d+)", question, re.IGNORECASE)
            if crew_match:
                crew_id = int(crew_match.group(1))
                crew = db.query(models.Crew).filter(models.Crew.crew_id == crew_id).first()
                if crew:
                    # Get crew qualifications
                    qualifications = db.query(models.CrewQualification).filter(
                        models.CrewQualification.crew_id == crew_id
                    ).all()
                    
                    # Get crew preferences
                    from datetime import date
                    today = date.today()
                    preferences = db.query(models.CrewPreference).filter(
                        models.CrewPreference.crew_id == crew_id,
                        (models.CrewPreference.valid_from.is_(None) | (models.CrewPreference.valid_from <= today)),
                        (models.CrewPreference.valid_to.is_(None) | (models.CrewPreference.valid_to >= today))
                    ).all()
                    
                    ctx["enhanced_data"]["crew_details"] = {
                        "crew_id": crew.crew_id,
                        "emp_code": crew.emp_code,
                        "name": crew.name,
                        "rank": crew.rank,
                        "base_iata": crew.base_iata,
                        "status": crew.status,
                        "qualifications": [{"aircraft_code": q.aircraft_code, "qualified_on": str(q.qualified_on)} for q in qualifications],
                        "preferences": [{"type": p.preference_type, "value": p.preference_value, "weight": p.weight} for p in preferences]
                    }
        else:
            # Get some active crew members
            active_crew = db.query(models.Crew).filter(models.Crew.status == "Active").limit(5).all()
            ctx["enhanced_data"]["active_crew"] = [
                {
                    "crew_id": c.crew_id,
                    "emp_code": c.emp_code,
                    "name": c.name,
                    "rank": c.rank,
                    "base_iata": c.base_iata
                }
                for c in active_crew
            ]
    
    if "aircraft" in q_lower:
        # Add aircraft-related data
        if "code" in q_lower or "type" in q_lower:
            # Try to extract aircraft code from question
            import re
            aircraft_match = re.search(r"[A-Z0-9]{3,4}", question)
            if aircraft_match:
                aircraft_code = aircraft_match.group(0).upper()
                aircraft = db.query(models.AircraftType).filter(models.AircraftType.code == aircraft_code).first()
                if aircraft:
                    ctx["enhanced_data"]["aircraft_details"] = {
                        "code": aircraft.code,
                        "description": aircraft.description
                    }
        else:
            # Get all aircraft types
            aircraft_types = db.query(models.AircraftType).all()
            ctx["enhanced_data"]["aircraft_types"] = [
                {"code": a.code, "description": a.description}
                for a in aircraft_types
            ]
    
    return ctx
