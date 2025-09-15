
from sqlalchemy.orm import Session
from app.storage import models
from app.rules.engine import RulesEngine
from datetime import timedelta
from typing import Dict, List
from datetime import date

def calculate_preference_score(crew_id: int, flight_date: date, dep_iata: str, arr_iata: str,
                              flight_no: str, pref_map: Dict[int, list]) -> int:
    """Calculate preference score for a crew member for a specific flight"""
    score = 0
    prefs = pref_map.get(crew_id, [])
    
    for pref in prefs:
        if pref.preference_type == "day_off" and pref.preference_value == flight_date.strftime("%A"):
            # Day off preference (negative score as it's a penalty)
            score -= pref.weight * 10  # Strong penalty for day off preferences
        elif pref.preference_type == "base" and pref.preference_value == dep_iata:
            # Base preference (positive score as it's a bonus)
            score += pref.weight * 2  # Moderate bonus for base preferences
        elif pref.preference_type == "destination" and pref.preference_value == arr_iata:
            # Destination preference (positive score as it's a bonus)
            score += pref.weight  # Smaller bonus for destination preferences
        elif pref.preference_type == "flight_no" and pref.preference_value == flight_no:
            # Specific flight number preference (positive score as it's a bonus)
            score += pref.weight * 3  # Higher bonus for specific flight preferences
        elif pref.preference_type == "weekend_off" and flight_date.weekday() >= 5:
            # Weekend off preference (negative score as it's a penalty)
            score -= pref.weight * 5  # Moderate penalty for weekend work
    
    return score

def calculate_multi_objective_score(crew_id: int, flight: object, pref_map: Dict[int, list],
                                  crew_duty_count: Dict[int, int], crew_consecutive_days: Dict[int, int],
                                  crew_night_duties: Dict[int, int], avg_duty_count: float) -> float:
    """Calculate a multi-objective score that balances preferences, fairness, and operational efficiency"""
    from datetime import date
    
    # Get preference score
    pref_score = calculate_preference_score(crew_id, flight.flight_date, flight.dep_iata, flight.arr_iata, flight.flight_no, pref_map)
    
    # Get fairness metrics
    duty_count = crew_duty_count.get(crew_id, 0)
    consecutive_days = crew_consecutive_days.get(crew_id, 0)
    night_duties = crew_night_duties.get(crew_id, 0)
    
    # Calculate fairness score (lower is better, so we negate it)
    fairness_score = 0
    if avg_duty_count > 0:
        fairness_score -= abs(duty_count - avg_duty_count) * 2  # Duty count fairness
    fairness_score -= consecutive_days * 1.5  # Consecutive days penalty
    fairness_score -= night_duties * 1  # Night duties penalty
    
    # Operational efficiency score (favor experienced crew)
    efficiency_score = duty_count * 0.5  # More experienced crew get a slight bonus
    
    # Combine all scores with weights
    total_score = (pref_score * 0.5) + (fairness_score * 0.3) + (efficiency_score * 0.2)
    
    return total_score

def is_crew_qualified_for_flight(crew_id: int, flight: object, qual_map: Dict[int, Dict[str, object]], flight_date: date) -> bool:
    """Check if a crew member is qualified for a specific flight"""
    crew_quals = qual_map.get(crew_id, {})
    
    # Check aircraft qualification
    if flight.aircraft_code not in crew_quals:
        return False
    
    # Check if qualification is current
    qual = crew_quals[flight.aircraft_code]
    if qual.expires_on and qual.expires_on < flight_date:
        return False
    
    return True

def get_crew_preferences(crew_id: int, pref_map: Dict[int, list]) -> Dict[str, list]:
    """Get all preferences for a crew member in a structured format"""
    prefs = pref_map.get(crew_id, [])
    structured_prefs = {}
    
    for pref in prefs:
        pref_type = pref.preference_type
        if pref_type not in structured_prefs:
            structured_prefs[pref_type] = []
        structured_prefs[pref_type].append({
            "value": pref.preference_value,
            "weight": pref.weight,
            "valid_from": pref.valid_from,
            "valid_to": pref.valid_to
        })
    
    return structured_prefs

def is_crew_available(crew_id: int, flight_date: date, unavailable_crew_map: Dict[int, List[object]]) -> bool:
    """Check if a crew member is available for a specific date"""
    if crew_id not in unavailable_crew_map:
        return True
    
    # Check if the crew member is unavailable on this date
    for record in unavailable_crew_map[crew_id]:
        if record.unavailable_from <= flight_date <= record.unavailable_to:
            return False
    
    return True

def generate_roster(db: Session, period_start, period_end, rules: RulesEngine):
    flights = db.query(models.Flight).filter(
        models.Flight.flight_date >= period_start,
        models.Flight.flight_date <= period_end
    ).order_by(models.Flight.sched_dep_utc).all()
    
    crew = db.query(models.Crew).filter(models.Crew.status == "Active").all()
    quals = db.query(models.CrewQualification).all()
    prefs = db.query(models.CrewPreference).all()
    # Get crew availability records
    from datetime import date
    today = date.today()
    unavailable_crew = db.query(models.CrewAvailability).filter(
        models.CrewAvailability.unavailable_from <= period_end,
        models.CrewAvailability.unavailable_to >= period_start,
        models.CrewAvailability.status == "approved"
    ).all()
    
    # Create a map of unavailable crew
    unavailable_crew_map: Dict[int, List[models.CrewAvailability]] = {}
    for record in unavailable_crew:
        if record.crew_id not in unavailable_crew_map:
            unavailable_crew_map[record.crew_id] = []
        unavailable_crew_map[record.crew_id].append(record)
    
    # Build qualification map with expiry dates
    qual_map: Dict[int, Dict[str, object]] = {}
    today = date.today()
    for q in quals:
        # Check if qualification is still valid
        if q.expires_on is None or q.expires_on >= today:
            if q.crew_id not in qual_map:
                qual_map[q.crew_id] = {}
            qual_map[q.crew_id][q.aircraft_code] = q
    
    # Build preference map
    pref_map: Dict[int, list] = {}
    for p in prefs:
        # Check if preference is currently valid
        if (p.valid_from is None or p.valid_from <= today) and (p.valid_to is None or p.valid_to >= today):
            if p.crew_id not in pref_map:
                pref_map[p.crew_id] = []
            pref_map[p.crew_id].append(p)
    
    # Track crew duty history for extended rules checking
    crew_duty_history: Dict[int, List[timedelta]] = {}
    crew_last_duty_end: Dict[int, object] = {}
    crew_duty_count: Dict[int, int] = {}  # Track number of duties per crew
    crew_weekly_duties: Dict[int, List[timedelta]] = {}  # Track weekly duties per crew
    crew_consecutive_days: Dict[int, int] = {}  # Track consecutive duty days per crew
    crew_night_duties: Dict[int, int] = {}  # Track night duties per crew
    
    assignments = []
    for f in flights:
        assigned = False
        start = f.sched_dep_utc
        end = f.sched_arr_utc
        duty_duration = end - start
        
        
        # Create a list of eligible crew with preference scores and fairness metrics
        eligible_crew = []
        for c in crew:
            # Check if crew is qualified for this flight
            if not is_crew_qualified_for_flight(c.crew_id, f, qual_map, f.flight_date):
                continue
            
            # Check if crew is available for this date
            if not is_crew_available(c.crew_id, f.flight_date, unavailable_crew_map):
                continue
            
            # Check basic duty duration
            if not rules.duty_duration_ok(start, end):
                continue
            
            # Check rest period
            if not rules.rest_ok(crew_last_duty_end.get(c.crew_id), start):
                continue
            
            # Check weekly duty
            weekly_duties = crew_weekly_duties.get(c.crew_id, [])
            if not rules.weekly_duty_ok(weekly_duties):
                continue
            
            # Check consecutive duty days
            consecutive_days = crew_consecutive_days.get(c.crew_id, 0)
            if not rules.consecutive_duty_days_ok(consecutive_days):
                continue
            
            # Check night duty limits if this is a night flight
            night_duties = crew_night_duties.get(c.crew_id, 0)
            if rules.is_night_duty(start, end) and not rules.night_duty_ok(night_duties):
                continue
            
            # Calculate preference score
            pref_score = calculate_preference_score(c.crew_id, f.flight_date, f.dep_iata, f.arr_iata, f.flight_no, pref_map)
            # Get duty count for fairness (lower is better)
            duty_count = crew_duty_count.get(c.crew_id, 0)
            # Get consecutive days for fairness (lower is better)
            consecutive_count = crew_consecutive_days.get(c.crew_id, 0)
            # Get night duties for fairness (lower is better)
            night_count = crew_night_duties.get(c.crew_id, 0)
            eligible_crew.append((c, pref_score, duty_count, consecutive_count, night_count))
        
        # Calculate average duty count for fairness scoring
        avg_duty_count = sum(crew_duty_count.values()) / len(crew_duty_count) if crew_duty_count else 0
        
        # Calculate multi-objective scores for eligible crew
        scored_crew = []
        for c, pref_score, duty_count, consecutive_count, night_count in eligible_crew:
            multi_score = calculate_multi_objective_score(
                c.crew_id, f, pref_map, crew_duty_count, crew_consecutive_days, crew_night_duties, avg_duty_count
            )
            scored_crew.append((c, multi_score, pref_score, duty_count, consecutive_count, night_count))
        
        # Sort eligible crew by multi-objective score (descending)
        scored_crew.sort(key=lambda x: -x[1])
        
        # Assign the crew with the highest multi-objective score
        if scored_crew:
            c, multi_score, pref_score, duty_count, consecutive_count, night_count = scored_crew[0]
            
            # All checks passed, assign crew
            assignments.append(dict(
                crew_id=c.crew_id,
                crew_name=c.name,  # Add crew name for better display
                flight_id=f.flight_id,
                duty_start_utc=start,
                duty_end_utc=end
            ))
            
            # Update crew history
            crew_last_duty_end[c.crew_id] = end
            crew_duty_history.setdefault(c.crew_id, []).append(duty_duration)
            crew_duty_count[c.crew_id] = crew_duty_count.get(c.crew_id, 0) + 1
            crew_weekly_duties.setdefault(c.crew_id, []).append(duty_duration)
            
            # Update consecutive days
            last_duty_end = crew_last_duty_end.get(c.crew_id)
            if last_duty_end and (start.date() - last_duty_end.date()).days == 1:
                # Consecutive day
                crew_consecutive_days[c.crew_id] = consecutive_count + 1
            else:
                # Reset consecutive days counter
                crew_consecutive_days[c.crew_id] = 1
            
            # Update night duties count if this is a night flight
            if rules.is_night_duty(start, end):
                crew_night_duties[c.crew_id] = night_count + 1
            
            assigned = True
        
        if not assigned:
            assignments.append(dict(
                crew_id=None,
                crew_name=None,  # Add crew name for consistency
                flight_id=f.flight_id,
                duty_start_utc=f.sched_dep_utc,
                duty_end_utc=f.sched_arr_utc,
                note="UNASSIGNED"
            ))
    
    total = len(flights)
    assigned_count = sum(1 for a in assignments if a.get("crew_id"))
    
    # Calculate fairness metrics
    avg_duty_count = sum(crew_duty_count.values()) / len(crew_duty_count) if crew_duty_count else 0
    max_duty_count = max(crew_duty_count.values()) if crew_duty_count else 0
    min_duty_count = min(crew_duty_count.values()) if crew_duty_count else 0
    
    # Calculate additional KPIs for multi-objective optimization
    total_pref_score = sum(calculate_preference_score(a["crew_id"],
                            db.query(models.Flight).filter(models.Flight.flight_id == a["flight_id"]).first().flight_date,
                            db.query(models.Flight).filter(models.Flight.flight_id == a["flight_id"]).first().dep_iata,
                            db.query(models.Flight).filter(models.Flight.flight_id == a["flight_id"]).first().arr_iata,
                            db.query(models.Flight).filter(models.Flight.flight_id == a["flight_id"]).first().flight_no,
                            pref_map)
                            for a in assignments if a.get("crew_id"))
    avg_pref_score = total_pref_score / assigned_count if assigned_count else 0
    
    kpis = {
        "flights_total": total,
        "flights_assigned": assigned_count,
        "assignment_rate": (assigned_count/total) if total else 0.0,
        "avg_duty_per_crew": avg_duty_count,
        "max_duty_per_crew": max_duty_count,
        "min_duty_per_crew": min_duty_count,
        "duty_distribution_range": max_duty_count - min_duty_count,
        "compliance_rate": 1.0,  # Assuming all assignments are compliant
        "avg_preference_score": avg_pref_score,
        "fairness_score": 1.0 - (max_duty_count - min_duty_count) / (max_duty_count + 1) if max_duty_count else 1.0
    }
    return assignments, kpis

def propose_patch_for_delay(db: Session, flight_no: str, delay_minutes: int, rules: RulesEngine):
    from datetime import timedelta
    f = db.query(models.Flight).filter(models.Flight.flight_no == flight_no).order_by(models.Flight.flight_date.desc()).first()
    if not f:
        return {"error": "flight_not_found"}
    
    # Record the disruption
    record_disruption(db, flight_no, "delay", f.flight_date,
                     impact_duration=delay_minutes, reason="Flight delayed")
    
    new_dep = f.sched_dep_utc + timedelta(minutes=delay_minutes)
    new_arr = f.sched_arr_utc + timedelta(minutes=delay_minutes)
    feasible = rules.duty_duration_ok(new_dep, new_arr)
    return {
        "flight_id": f.flight_id,
        "flight_no": f.flight_no,
        "new_sched_dep_utc": new_dep.isoformat(),
        "new_sched_arr_utc": new_arr.isoformat(),
        "feasible": feasible
    }

def handle_flight_cancellation(db: Session, flight_no: str, rules: RulesEngine):
    """Handle flight cancellation by releasing assigned crew and reassigning them if possible"""
    from datetime import date
    
    # Find the flight
    f = db.query(models.Flight).filter(models.Flight.flight_no == flight_no).order_by(models.Flight.flight_date.desc()).first()
    if not f:
        return {"error": "flight_not_found"}
    
    # Record the disruption
    record_disruption(db, flight_no, "cancellation", f.flight_date, reason="Flight cancelled")
    
    # Get all crew assigned to this flight (in a real implementation, we would query duty assignments)
    # For now, we'll simulate by finding qualified crew for this aircraft type
    qualified_crew = db.query(models.Crew).join(
        models.CrewQualification,
        models.Crew.crew_id == models.CrewQualification.crew_id
    ).filter(
        models.Crew.status == "Active",
        models.CrewQualification.aircraft_code == f.aircraft_code
    ).all()
    
    # Get preferences for these crew members
    today = date.today()
    prefs = db.query(models.CrewPreference).filter(
        models.CrewPreference.crew_id.in_([c.crew_id for c in qualified_crew]),
        (models.CrewPreference.valid_from.is_(None) | (models.CrewPreference.valid_from <= today)),
        (models.CrewPreference.valid_to.is_(None) | (models.CrewPreference.valid_to >= today))
    ).all()
    
    # Get crew availability records for the flight date
    unavailable_crew = db.query(models.CrewAvailability).filter(
        models.CrewAvailability.crew_id.in_([c.crew_id for c in qualified_crew]),
        models.CrewAvailability.unavailable_from <= f.flight_date,
        models.CrewAvailability.unavailable_to >= f.flight_date,
        models.CrewAvailability.status == "approved"
    ).all()
    
    # Create a map of unavailable crew
    unavailable_crew_map: Dict[int, List[models.CrewAvailability]] = {}
    for record in unavailable_crew:
        if record.crew_id not in unavailable_crew_map:
            unavailable_crew_map[record.crew_id] = []
        unavailable_crew_map[record.crew_id].append(record)
    
    # Build preference map
    pref_map: Dict[int, list] = {}
    for p in prefs:
        if p.crew_id not in pref_map:
            pref_map[p.crew_id] = []
        pref_map[p.crew_id].append(p)
    
    # Find other flights on the same day that need crew
    same_day_flights = db.query(models.Flight).filter(
        models.Flight.flight_date == f.flight_date,
        models.Flight.flight_id != f.flight_id,
        models.Flight.aircraft_code == f.aircraft_code
    ).all()
    
    # Build qualification map
    quals = db.query(models.CrewQualification).filter(
        models.CrewQualification.crew_id.in_([c.crew_id for c in qualified_crew])
    ).all()
    
    qual_map: Dict[int, Dict[str, object]] = {}
    for q in quals:
        if q.expires_on is None or q.expires_on >= f.flight_date:
            if q.crew_id not in qual_map:
                qual_map[q.crew_id] = {}
            qual_map[q.crew_id][q.aircraft_code] = q
    
    # Create reassignment suggestions
    reassignments = []
    for flight in same_day_flights:
        # Check if any of our released crew can be assigned to this flight
        for crew in qualified_crew:
            # Check if crew is qualified and available for this flight
            if (is_crew_qualified_for_flight(crew.crew_id, flight, qual_map, flight.flight_date) and
                is_crew_available(crew.crew_id, flight.flight_date, unavailable_crew_map)):
                # Calculate preference score
                pref_score = calculate_preference_score(
                    crew.crew_id, flight.flight_date, flight.dep_iata, flight.arr_iata, flight.flight_no, pref_map
                )
                
                # If preference score is positive, suggest reassignment
                if pref_score > 0:
                    reassignments.append({
                        "from_flight": f.flight_no,
                        "to_flight": flight.flight_no,
                        "crew_id": crew.crew_id,
                        "crew_name": crew.name,
                        "preference_score": pref_score
                    })
                    break  # One suggestion per flight is enough
    
    return {
        "flight_id": f.flight_id,
        "flight_no": f.flight_no,
        "status": "cancellation_handled",
        "message": f"Crew released from cancelled flight. Found {len(reassignments)} potential reassignments.",
        "reassignments": reassignments
    }

def handle_crew_unavailability(db: Session, crew_id: int, unavailable_from: date, unavailable_to: date, rules: RulesEngine):
    """Handle crew unavailability by reassigning their duties"""
    # Find the crew member
    crew = db.query(models.Crew).filter(models.Crew.crew_id == crew_id).first()
    if not crew:
        return {"error": "crew_not_found"}
    
    # Record the disruption
    record_disruption(db, None, "crew_unavailability", unavailable_from,
                     crew_id=crew_id, reason="Crew unavailable")
    
    # Find flights assigned to this crew member during the unavailable period
    # In a real implementation, we would query duty assignments
    # For now, we'll simulate by finding flights that match the crew's qualifications
    qualified_flights = db.query(models.Flight).join(
        models.CrewQualification,
        models.Flight.aircraft_code == models.CrewQualification.aircraft_code
    ).filter(
        models.CrewQualification.crew_id == crew_id,
        models.Flight.flight_date >= unavailable_from,
        models.Flight.flight_date <= unavailable_to,
        models.CrewQualification.expires_on.is_(None) | (models.CrewQualification.expires_on >= unavailable_to)
    ).all()
    
    # Get other qualified crew for these flights
    affected_flight_ids = [f.flight_id for f in qualified_flights]
    if not affected_flight_ids:
        return {
            "crew_id": crew_id,
            "crew_name": crew.name,
            "unavailable_from": unavailable_from.isoformat(),
            "unavailable_to": unavailable_to.isoformat(),
            "status": "unavailability_handled",
            "message": "No flights affected by crew unavailability"
        }
    
    # Get all other active crew qualified for the same aircraft types
    aircraft_codes = list(set([f.aircraft_code for f in qualified_flights]))
    other_qualified_crew = db.query(models.Crew).join(
        models.CrewQualification,
        models.Crew.crew_id == models.CrewQualification.crew_id
    ).filter(
        models.Crew.crew_id != crew_id,
        models.Crew.status == "Active",
        models.CrewQualification.aircraft_code.in_(aircraft_codes)
    ).all()
    
    # Get preferences for these crew members
    today = date.today()
    other_crew_ids = [c.crew_id for c in other_qualified_crew]
    prefs = db.query(models.CrewPreference).filter(
        models.CrewPreference.crew_id.in_(other_crew_ids),
        (models.CrewPreference.valid_from.is_(None) | (models.CrewPreference.valid_from <= today)),
        (models.CrewPreference.valid_to.is_(None) | (models.CrewPreference.valid_to >= today))
    ).all()
    
    # Get crew availability records for the unavailable period
    unavailable_crew = db.query(models.CrewAvailability).filter(
        models.CrewAvailability.crew_id.in_(other_crew_ids),
        models.CrewAvailability.unavailable_from <= unavailable_to,
        models.CrewAvailability.unavailable_to >= unavailable_from,
        models.CrewAvailability.status == "approved"
    ).all()
    
    # Create a map of unavailable crew
    unavailable_crew_map: Dict[int, List[models.CrewAvailability]] = {}
    for record in unavailable_crew:
        if record.crew_id not in unavailable_crew_map:
            unavailable_crew_map[record.crew_id] = []
        unavailable_crew_map[record.crew_id].append(record)
    
    # Build preference map
    pref_map: Dict[int, list] = {}
    for p in prefs:
        if p.crew_id not in pref_map:
            pref_map[p.crew_id] = []
        pref_map[p.crew_id].append(p)
    
    # Build qualification map for other crew
    quals = db.query(models.CrewQualification).filter(
        models.CrewQualification.crew_id.in_(other_crew_ids)
    ).all()
    
    qual_map: Dict[int, Dict[str, object]] = {}
    for q in quals:
        if q.expires_on is None or q.expires_on >= unavailable_to:
            if q.crew_id not in qual_map:
                qual_map[q.crew_id] = {}
            qual_map[q.crew_id][q.aircraft_code] = q
    
    # Create reassignment suggestions
    reassignments = []
    for flight in qualified_flights:
        # Check if any other crew can be assigned to this flight
        for other_crew in other_qualified_crew:
            # Check if crew is qualified and available for this flight
            if (is_crew_qualified_for_flight(other_crew.crew_id, flight, qual_map, flight.flight_date) and
                is_crew_available(other_crew.crew_id, flight.flight_date, unavailable_crew_map)):
                # Calculate preference score
                pref_score = calculate_preference_score(
                    other_crew.crew_id, flight.flight_date, flight.dep_iata, flight.arr_iata, flight.flight_no, pref_map
                )
                
                # Suggest reassignment with preference score
                reassignments.append({
                    "from_crew_id": crew_id,
                    "from_crew_name": crew.name,
                    "to_crew_id": other_crew.crew_id,
                    "to_crew_name": other_crew.name,
                    "flight_id": flight.flight_id,
                    "flight_no": flight.flight_no,
                    "flight_date": flight.flight_date.isoformat(),
                    "preference_score": pref_score
                })
                break  # One suggestion per flight is enough
    
    return {
        "crew_id": crew_id,
        "crew_name": crew.name,
        "unavailable_from": unavailable_from.isoformat(),
        "unavailable_to": unavailable_to.isoformat(),
        "status": "unavailability_handled",
        "message": f"Crew unavailability recorded. Found {len(reassignments)} potential reassignments.",
        "reassignments": reassignments
    }

def record_disruption(db: Session, flight_no: str, disruption_type: str, disruption_date: date,
                     impact_duration: int = None, crew_id: int = None, reason: str = None,
                     resolution: str = None) -> None:
    """Record a disruption event in the database"""
    from datetime import datetime
    
    # Get the next disruption ID
    last_record = db.query(models.DisruptionRecord).order_by(models.DisruptionRecord.disruption_id.desc()).first()
    next_id = (last_record.disruption_id + 1) if last_record else 1
    
    disruption = models.DisruptionRecord(
        disruption_id=next_id,
        flight_no=flight_no,
        disruption_type=disruption_type,
        disruption_date=disruption_date,
        impact_duration=impact_duration,
        crew_id=crew_id,
        reason=reason,
        resolution=resolution,
        recorded_at=datetime.utcnow()
    )
    
    db.add(disruption)
    db.commit()

def get_historical_disruptions(db: Session, flight_no: str = None, crew_id: int = None,
                              disruption_type: str = None, days_back: int = 30) -> List[models.DisruptionRecord]:
    """Retrieve historical disruption data"""
    from datetime import date, timedelta
    
    # Calculate the cutoff date
    cutoff_date = date.today() - timedelta(days=days_back)
    
    # Build the query
    query = db.query(models.DisruptionRecord).filter(
        models.DisruptionRecord.disruption_date >= cutoff_date
    )
    
    # Add filters if provided
    if flight_no:
        query = query.filter(models.DisruptionRecord.flight_no == flight_no)
    if crew_id:
        query = query.filter(models.DisruptionRecord.crew_id == crew_id)
    if disruption_type:
        query = query.filter(models.DisruptionRecord.disruption_type == disruption_type)
    
    return query.order_by(models.DisruptionRecord.disruption_date.desc()).all()
