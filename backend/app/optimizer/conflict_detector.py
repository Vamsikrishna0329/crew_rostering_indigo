"""
Conflict detection module that uses the hard/soft rule engine to identify violations.
"""
from sqlalchemy.orm import Session
from app.storage import models
from app.rules.hard_soft_engine import HardSoftRulesEngine
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

def detect_conflicts(db: Session, period_start: date, period_end: date, 
                    rules_engine: HardSoftRulesEngine = None) -> List[Dict]:
    """
    Detect conflicts and violations in the roster for a given period.
    
    Args:
        db: Database session
        period_start: Start date of the period to check
        period_end: End date of the period to check
        rules_engine: HardSoftRulesEngine instance (optional)
        
    Returns:
        List of conflicts with details
    """
    if rules_engine is None:
        rules_engine = HardSoftRulesEngine()
    
    conflicts = []
    
    # Get all duty periods for the period
    duty_periods = db.query(
        models.DutyPeriod,
        models.Flight,
        models.Crew
    ).select_from(
        models.DutyPeriod
    ).join(
        models.DutyFlight, models.DutyPeriod.duty_id == models.DutyFlight.duty_id
    ).join(
        models.Flight, models.DutyFlight.flight_id == models.Flight.flight_id
    ).join(
        models.Crew, models.DutyPeriod.crew_id == models.Crew.crew_id
    ).filter(
        models.DutyPeriod.duty_start_utc >= period_start,
        models.DutyPeriod.duty_end_utc <= period_end
    ).all()
    
    # Group duty periods by crew for analysis
    crew_duties = {}
    for duty, flight, crew in duty_periods:
        if crew.crew_id not in crew_duties:
            crew_duties[crew.crew_id] = {
                "crew": crew,
                "duties": [],
                "weekly_duties": {},
                "monthly_duties": {},
                "night_duties": {}
            }
        crew_duties[crew.crew_id]["duties"].append((duty, flight))
        
        # Track weekly and monthly duties
        week_key = duty.duty_start_utc.isocalendar()[:2]  # (year, week)
        month_key = (duty.duty_start_utc.year, duty.duty_start_utc.month)
        
        if week_key not in crew_duties[crew.crew_id]["weekly_duties"]:
            crew_duties[crew.crew_id]["weekly_duties"][week_key] = []
        crew_duties[crew.crew_id]["weekly_duties"][week_key].append(duty)
        
        if month_key not in crew_duties[crew.crew_id]["monthly_duties"]:
            crew_duties[crew.crew_id]["monthly_duties"][month_key] = []
        crew_duties[crew.crew_id]["monthly_duties"][month_key].append(duty)
        
        # Track night duties
        if rules_engine.is_night_duty(duty.duty_start_utc, duty.duty_end_utc):
            week_key = duty.duty_start_utc.isocalendar()[:2]
            if week_key not in crew_duties[crew.crew_id]["night_duties"]:
                crew_duties[crew.crew_id]["night_duties"][week_key] = 0
            crew_duties[crew.crew_id]["night_duties"][week_key] += 1
    
    # Check for conflicts for each crew
    for crew_id, crew_data in crew_duties.items():
        crew = crew_data["crew"]
        duties = crew_data["duties"]
        
        # Sort duties by start time
        duties.sort(key=lambda x: x[0].duty_start_utc)
        
        # Check for overlapping duties (hard rule violation)
        for i in range(len(duties) - 1):
            current_duty, current_flight = duties[i]
            next_duty, next_flight = duties[i + 1]
            
            # Check if duties overlap
            if current_duty.duty_end_utc > next_duty.duty_start_utc:
                conflicts.append({
                    "type": "overlapping_duties",
                    "crew_id": crew_id,
                    "crew_name": crew.name,
                    "description": f"Overlapping duties: {current_flight.flight_no} and {next_flight.flight_no}",
                    "severity": "high",
                    "flight_ids": [current_flight.flight_id, next_flight.flight_id],
                    "timestamp": current_duty.duty_start_utc.isoformat()
                })
        
        # Check individual duty compliance
        for duty, flight in duties:
            # Get weekly and monthly duty data for this duty
            week_key = duty.duty_start_utc.isocalendar()[:2]
            month_key = (duty.duty_start_utc.year, duty.duty_start_utc.month)
            
            weekly_duty_durations = [
                d.duty_end_utc - d.duty_start_utc 
                for d in crew_data["weekly_duties"].get(week_key, [])
            ]
            
            monthly_duty_durations = [
                d.duty_end_utc - d.duty_start_utc 
                for d in crew_data["monthly_duties"].get(month_key, [])
            ]
            
            weekly_night_duties = crew_data["night_duties"].get(week_key, 0)
            
            # Calculate consecutive duty days (simplified)
            consecutive_days = 1  # This would need more complex logic in a real implementation
            
            # Calculate average duty count for fairness (simplified)
            avg_duty_count = len(duties) / len(crew_duties) if crew_duties else 0
            
            # Check hard rule violations
            hard_violations = rules_engine.check_hard_rule_violations(
                duty.duty_start_utc,
                duty.duty_end_utc,
                crew.rank,
                consecutive_days,
                weekly_duty_durations,
                monthly_duty_durations,
                weekly_night_duties,
                duty.duty_end_utc - duty.duty_start_utc,  # weekly flight time (simplified)
                duty.duty_end_utc - duty.duty_start_utc   # monthly flight time (simplified)
            )
            
            # Add hard rule violations to conflicts
            for violation_type in hard_violations:
                conflicts.append({
                    "type": "hard_rule_violation",
                    "crew_id": crew_id,
                    "crew_name": crew.name,
                    "description": f"Hard rule violation: {violation_type.replace('_', ' ').title()}",
                    "severity": "high",
                    "flight_ids": [flight.flight_id],
                    "timestamp": duty.duty_start_utc.isoformat(),
                    "violation_type": violation_type
                })
            
            # Check soft rule violations (as warnings)
            soft_penalties = rules_engine.check_soft_rule_violations(
                duty.duty_start_utc,
                duty.duty_end_utc,
                crew.rank,
                consecutive_days,
                weekly_night_duties,
                len(duties),
                avg_duty_count
            )
            
            # Add soft rule violations as medium severity conflicts
            for penalty_type, penalty_value in soft_penalties.items():
                if penalty_value > 0:  # Only add if there's actually a penalty
                    conflicts.append({
                        "type": "soft_rule_violation",
                        "crew_id": crew_id,
                        "crew_name": crew.name,
                        "description": f"Soft rule concern: {penalty_type.replace('_', ' ').title()} (Penalty: {penalty_value:.1f})",
                        "severity": "medium",
                        "flight_ids": [flight.flight_id],
                        "timestamp": duty.duty_start_utc.isoformat(),
                        "penalty_type": penalty_type,
                        "penalty_value": penalty_value
                    })
    
    # Check for qualification mismatches (hard rule)
    qualifications = db.query(models.CrewQualification).all()
    qual_map = {}
    for q in qualifications:
        if q.crew_id not in qual_map:
            qual_map[q.crew_id] = {}
        qual_map[q.crew_id][q.aircraft_code] = q
    
    for duty, flight, crew in duty_periods:
        # Check if crew is qualified for the aircraft
        if crew.crew_id in qual_map and flight.aircraft_code in qual_map[crew.crew_id]:
            qual = qual_map[crew.crew_id][flight.aircraft_code]
            if qual.expires_on and qual.expires_on < flight.flight_date:
                conflicts.append({
                    "type": "qualification_mismatch",
                    "crew_id": crew.crew_id,
                    "crew_name": crew.name,
                    "description": f"Assigned to {flight.aircraft_code} without valid qualification",
                    "severity": "high",
                    "flight_ids": [flight.flight_id],
                    "timestamp": duty.duty_start_utc.isoformat()
                })
        else:
            conflicts.append({
                "type": "qualification_mismatch",
                "crew_id": crew.crew_id,
                "crew_name": crew.name,
                "description": f"Assigned to {flight.aircraft_code} without required qualification",
                "severity": "high",
                "flight_ids": [flight.flight_id],
                "timestamp": duty.duty_start_utc.isoformat()
            })
    
    return conflicts

def get_conflict_summary(conflicts: List[Dict]) -> Dict:
    """
    Generate a summary of conflicts by type and severity.
    
    Args:
        conflicts: List of conflicts
        
    Returns:
        Summary dictionary
    """
    summary = {
        "total_conflicts": len(conflicts),
        "by_severity": {
            "high": 0,
            "medium": 0,
            "low": 0
        },
        "by_type": {},
        "crew_affected": set()
    }
    
    for conflict in conflicts:
        # Count by severity
        severity = conflict.get("severity", "low")
        summary["by_severity"][severity] += 1
        
        # Count by type
        conflict_type = conflict.get("type", "unknown")
        if conflict_type not in summary["by_type"]:
            summary["by_type"][conflict_type] = 0
        summary["by_type"][conflict_type] += 1
        
        # Track affected crew
        if "crew_id" in conflict:
            summary["crew_affected"].add(conflict["crew_id"])
    
    summary["crew_affected"] = len(summary["crew_affected"])
    
    return summary

def filter_conflicts(conflicts: List[Dict], severity: str = None, conflict_type: str = None) -> List[Dict]:
    """
    Filter conflicts by severity and/or type.
    
    Args:
        conflicts: List of conflicts
        severity: Severity to filter by (high, medium, low)
        conflict_type: Type to filter by
        
    Returns:
        Filtered list of conflicts
    """
    filtered = conflicts
    
    if severity:
        filtered = [c for c in filtered if c.get("severity") == severity]
    
    if conflict_type:
        filtered = [c for c in filtered if c.get("type") == conflict_type]
    
    return filtered