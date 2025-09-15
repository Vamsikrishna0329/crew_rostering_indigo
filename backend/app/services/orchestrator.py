
from sqlalchemy.orm import Session
from app.rules.engine import RulesEngine
from app.rules.hard_soft_engine import HardSoftRulesEngine
from app.optimizer import generate_roster, generate_roster_with_or_tools, propose_patch_for_delay, handle_flight_cancellation, handle_crew_unavailability
from app.storage import models
from app.storage.models import DGCAConstraints, DutyPeriod, DutyFlight
from datetime import date

def build_rules(db: Session, version: str) -> RulesEngine:
    row = db.query(DGCAConstraints).filter(DGCAConstraints.version == version).first()
    if row:
        return RulesEngine(
            max_duty_hours_per_day=float(row.max_duty_hours_per_day),
            min_rest_hours_after_duty=float(row.min_rest_hours_after_duty),
            max_fdp_hours=float(row.max_fdp_hours),
            max_duty_hours_per_week=float(row.max_duty_hours_per_week) if row.max_duty_hours_per_week else None,
            max_duty_hours_per_month=float(row.max_duty_hours_per_month) if row.max_duty_hours_per_month else None,
            max_consecutive_duty_days=int(row.max_consecutive_duty_days) if row.max_consecutive_duty_days else None,
            min_rest_hours_between_duties=float(row.min_rest_hours_between_duties) if row.min_rest_hours_between_duties else None,
            max_night_duties_per_week=int(row.max_night_duties_per_week) if row.max_night_duties_per_week else None,
            min_rest_hours_after_night_duty=float(row.min_rest_hours_after_night_duty) if row.min_rest_hours_after_night_duty else None,
            max_extended_fdp_hours=float(row.max_extended_fdp_hours) if row.max_extended_fdp_hours else None,
            max_flight_time_per_day=float(row.max_flight_time_per_day) if row.max_flight_time_per_day else None,
            max_flight_time_per_week=float(row.max_flight_time_per_week) if row.max_flight_time_per_week else None,
            max_flight_time_per_month=float(row.max_flight_time_per_month) if row.max_flight_time_per_month else None
        )
    return RulesEngine()

def build_hard_soft_rules(db: Session, version: str) -> HardSoftRulesEngine:
    row = db.query(DGCAConstraints).filter(DGCAConstraints.version == version).first()
    if row:
        return HardSoftRulesEngine(
            max_duty_hours_per_day=float(row.max_duty_hours_per_day),
            min_rest_hours_after_duty=float(row.min_rest_hours_after_duty),
            max_fdp_hours=float(row.max_fdp_hours),
            max_duty_hours_per_week=float(row.max_duty_hours_per_week) if row.max_duty_hours_per_week else None,
            max_duty_hours_per_month=float(row.max_duty_hours_per_month) if row.max_duty_hours_per_month else None,
            max_consecutive_duty_days=int(row.max_consecutive_duty_days) if row.max_consecutive_duty_days else None,
            min_rest_hours_between_duties=float(row.min_rest_hours_between_duties) if row.min_rest_hours_between_duties else None,
            max_night_duties_per_week=int(row.max_night_duties_per_week) if row.max_night_duties_per_week else None,
            min_rest_hours_after_night_duty=float(row.min_rest_hours_after_night_duty) if row.min_rest_hours_after_night_duty else None,
            max_extended_fdp_hours=float(row.max_extended_fdp_hours) if row.max_extended_fdp_hours else None,
            max_flight_time_per_day=float(row.max_flight_time_per_day) if row.max_flight_time_per_day else None,
            max_flight_time_per_week=float(row.max_flight_time_per_week) if row.max_flight_time_per_week else None,
            max_flight_time_per_month=float(row.max_flight_time_per_month) if row.max_flight_time_per_month else None
        )
    return HardSoftRulesEngine()


def run_generate_roster_with_hard_soft_rules(db: Session, period_start, period_end, rules_version: str, optimization_method: str = "simple"):
    """Generate roster using hard/soft rule classification"""
    rules = build_hard_soft_rules(db, rules_version)
    
    # For now, we'll use the same optimization methods but pass the new rule engine
    # In a full implementation, we would modify the optimizers to use the new rule engine
    from app.rules.engine import RulesEngine
    legacy_rules = build_rules(db, rules_version)
    
    if optimization_method == "or_tools":
        assignments, kpis = generate_roster_with_or_tools(db, period_start, period_end, legacy_rules)
    else:
        assignments, kpis = generate_roster(db, period_start, period_end, legacy_rules)
    
    # Add rule classification information to KPIs
    rule_categories = rules.get_rule_categories()
    kpis["rule_classification"] = rule_categories
    
    return assignments, kpis

def run_detect_conflicts(db: Session, period_start, period_end, rules_version: str = "v1"):
    """Detect conflicts in the roster"""
    from app.optimizer.conflict_detector import detect_conflicts
    rules = build_hard_soft_rules(db, rules_version)
    conflicts = detect_conflicts(db, period_start, period_end, rules)
    return conflicts

def run_reroster_delay(db: Session, flight_no: str, delay_minutes: int, rules_version: str):
    rules = build_rules(db, rules_version)
    patch = propose_patch_for_delay(db, flight_no, delay_minutes, rules)
    kpis = {"changed_flights": 1 if "flight_id" in patch else 0}
    return patch, kpis

def run_handle_cancellation(db: Session, flight_no: str, rules_version: str):
    rules = build_rules(db, rules_version)
    result = handle_flight_cancellation(db, flight_no, rules)
    kpis = {"handled_cancellations": 1 if "error" not in result else 0}
    return result, kpis

def run_handle_crew_unavailability(db: Session, crew_id: int, unavailable_from: date, unavailable_to: date, rules_version: str):
    rules = build_rules(db, rules_version)
    result = handle_crew_unavailability(db, crew_id, unavailable_from, unavailable_to, rules)
    kpis = {"handled_unavailabilities": 1 if "error" not in result else 0}
    return result, kpis

def save_assignments_to_duty_tables(db: Session, assignments: list):
    """Save assignments to duty_period and duty_flight tables"""
    from datetime import datetime
    
    # Clear existing duty data for the period (if any)
    # In a production system, you might want to be more selective about this
    # For now, we'll clear all duty data
    db.query(DutyFlight).delete()
    db.query(DutyPeriod).delete()
    db.commit()
    
    # Group assignments by crew and create duty periods
    crew_duties = {}
    for assignment in assignments:
        if assignment.get("crew_id") and not assignment.get("note") == "UNASSIGNED":
            crew_id = assignment["crew_id"]
            if crew_id not in crew_duties:
                crew_duties[crew_id] = []
            crew_duties[crew_id].append(assignment)
    
    # Create duty periods and duty flights
    for crew_id, crew_assignments in crew_duties.items():
        if not crew_assignments:
            continue
            
        # Get crew base (for simplicity, we'll use the departure airport of the first flight)
        # In a real implementation, you would get the crew's actual base
        first_assignment = crew_assignments[0]
        flight = db.query(models.Flight).filter(models.Flight.flight_id == first_assignment["flight_id"]).first()
        crew = db.query(models.Crew).filter(models.Crew.crew_id == crew_id).first()
        base_iata = crew.base_iata if crew else (flight.dep_iata if flight else "DEL")
        
        # Create duty period (for now, we'll create one duty period per assignment)
        # In a more sophisticated implementation, you might group multiple flights into one duty period
        for assignment in crew_assignments:
            # Get the flight to get actual departure/arrival times
            flight = db.query(models.Flight).filter(models.Flight.flight_id == assignment["flight_id"]).first()
            if not flight:
                continue
                
            # Get the next duty ID
            last_duty = db.query(DutyPeriod).order_by(DutyPeriod.duty_id.desc()).first()
            next_duty_id = (last_duty.duty_id + 1) if last_duty else 1
                
            # Create duty period
            duty_period = DutyPeriod(
                duty_id=next_duty_id,
                crew_id=crew_id,
                duty_start_utc=assignment["duty_start_utc"],
                duty_end_utc=assignment["duty_end_utc"],
                base_iata=base_iata
            )
            db.add(duty_period)
            db.flush()  # Get the duty_id
            
            # Create duty flight
            duty_flight = DutyFlight(
                duty_id=duty_period.duty_id,
                flight_id=assignment["flight_id"],
                leg_seq=1  # For now, we assume one flight per duty
            )
            db.add(duty_flight)
    
    db.commit()

def run_generate_roster(db: Session, period_start, period_end, rules_version: str, optimization_method: str = "simple"):
    rules = build_rules(db, rules_version)
    
    if optimization_method == "or_tools":
        assignments, kpis = generate_roster_with_or_tools(db, period_start, period_end, rules)
    else:
        assignments, kpis = generate_roster(db, period_start, period_end, rules)
    
    # Save assignments to duty tables
    save_assignments_to_duty_tables(db, assignments)
    
    return assignments, kpis

def run_generate_roster_with_hard_soft_rules(db: Session, period_start, period_end, rules_version: str, optimization_method: str = "simple"):
    """Generate roster using hard/soft rule classification"""
    rules = build_hard_soft_rules(db, rules_version)
    
    # For now, we'll use the same optimization methods but pass the new rule engine
    # In a full implementation, we would modify the optimizers to use the new rule engine
    from app.rules.engine import RulesEngine
    legacy_rules = build_rules(db, rules_version)
    
    if optimization_method == "or_tools":
        assignments, kpis = generate_roster_with_or_tools(db, period_start, period_end, legacy_rules)
    else:
        assignments, kpis = generate_roster(db, period_start, period_end, legacy_rules)
    
    # Save assignments to duty tables
    save_assignments_to_duty_tables(db, assignments)
    
    # Add rule classification information to KPIs
    rule_categories = rules.get_rule_categories()
    kpis["rule_classification"] = rule_categories
    
    return assignments, kpis
