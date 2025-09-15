"""
Rule engine that distinguishes between hard rules (non-negotiable) and soft rules (preferences/fairness).
"""
from datetime import timedelta, datetime
from typing import Optional, List, Dict, Tuple
from app.storage import models

class HardSoftRulesEngine:
    def __init__(
        self,
        # Hard rules (DGCA/legal/compliance)
        max_duty_hours_per_day: float = 10.0,
        min_rest_hours_after_duty: float = 12.0,
        max_fdp_hours: float = 13.0,
        max_duty_hours_per_week: Optional[float] = None,
        max_duty_hours_per_month: Optional[float] = None,
        max_consecutive_duty_days: Optional[int] = None,
        min_rest_hours_between_duties: Optional[float] = None,
        max_night_duties_per_week: Optional[int] = None,
        min_rest_hours_after_night_duty: Optional[float] = None,
        max_extended_fdp_hours: Optional[float] = None,
        max_flight_time_per_day: Optional[float] = None,
        max_flight_time_per_week: Optional[float] = None,
        max_flight_time_per_month: Optional[float] = None,
        min_crew_per_flight: int = 2,  # Minimum crew per flight
        min_cabin_crew_per_aircraft: Dict[str, int] = None,  # Min cabin crew per aircraft type
        
        # Soft rules (preferences/fairness/efficiency)
        preferred_max_duty_hours_per_day: float = 8.0,
        preferred_max_consecutive_duty_days: int = 4,
        preferred_rest_hours_after_duty: float = 14.0,
        preferred_night_duties_per_week: int = 2,
        fairness_weight: float = 1.0,
        preference_weight: float = 1.0,
        efficiency_weight: float = 1.0
    ):
        # Hard rules - non-negotiable
        self.hard_rules = {
            "max_duty_per_day": timedelta(hours=max_duty_hours_per_day),
            "min_rest_after_duty": timedelta(hours=min_rest_hours_after_duty),
            "max_fdp": timedelta(hours=max_fdp_hours),
            "max_duty_per_week": timedelta(hours=max_duty_hours_per_week) if max_duty_hours_per_week else None,
            "max_duty_per_month": timedelta(hours=max_duty_hours_per_month) if max_duty_hours_per_month else None,
            "max_consecutive_duty_days": max_consecutive_duty_days,
            "min_rest_between_duties": timedelta(hours=min_rest_hours_between_duties) if min_rest_hours_between_duties else None,
            "max_night_duties_per_week": max_night_duties_per_week,
            "min_rest_after_night_duty": timedelta(hours=min_rest_hours_after_night_duty) if min_rest_hours_after_night_duty else None,
            "max_extended_fdp": timedelta(hours=max_extended_fdp_hours) if max_extended_fdp_hours else None,
            "max_flight_time_per_day": timedelta(hours=max_flight_time_per_day) if max_flight_time_per_day else None,
            "max_flight_time_per_week": timedelta(hours=max_flight_time_per_week) if max_flight_time_per_week else None,
            "max_flight_time_per_month": timedelta(hours=max_flight_time_per_month) if max_flight_time_per_month else None,
            "min_crew_per_flight": min_crew_per_flight,
            "min_cabin_crew_per_aircraft": min_cabin_crew_per_aircraft or {}
        }
        
        # Soft rules - preferences and fairness metrics
        self.soft_rules = {
            "preferred_max_duty_per_day": timedelta(hours=preferred_max_duty_hours_per_day),
            "preferred_max_consecutive_duty_days": preferred_max_consecutive_duty_days,
            "preferred_rest_after_duty": timedelta(hours=preferred_rest_hours_after_duty),
            "preferred_night_duties_per_week": preferred_night_duties_per_week,
            "fairness_weight": fairness_weight,
            "preference_weight": preference_weight,
            "efficiency_weight": efficiency_weight
        }
    
    def check_hard_rule_violations(self, duty_start: datetime, duty_end: datetime,
                                 crew_rank: str, consecutive_days: int,
                                 weekly_duties: List[timedelta],
                                 monthly_duties: List[timedelta],
                                 weekly_night_duties: int,
                                 weekly_flight_time: timedelta,
                                 monthly_flight_time: timedelta) -> Dict[str, bool]:
        """Check for violations of hard rules (must not be violated)"""
        violations = {}
        
        duty_duration = duty_end - duty_start
        
        # Basic duty duration checks
        if duty_duration > self.hard_rules["max_duty_per_day"]:
            violations["duty_duration_exceeded"] = True
            
        if duty_duration > self.hard_rules["max_fdp"]:
            violations["fdp_exceeded"] = True
        
        # Weekly duty checks
        if self.hard_rules["max_duty_per_week"]:
            total_weekly_duty = sum(weekly_duties, timedelta())
            if total_weekly_duty > self.hard_rules["max_duty_per_week"]:
                violations["weekly_duty_exceeded"] = True
        
        # Monthly duty checks
        if self.hard_rules["max_duty_per_month"]:
            total_monthly_duty = sum(monthly_duties, timedelta())
            if total_monthly_duty > self.hard_rules["max_duty_per_month"]:
                violations["monthly_duty_exceeded"] = True
        
        # Consecutive duty days
        if self.hard_rules["max_consecutive_duty_days"]:
            if consecutive_days > self.hard_rules["max_consecutive_duty_days"]:
                violations["consecutive_duty_days_exceeded"] = True
        
        # Weekly flight time
        if self.hard_rules["max_flight_time_per_week"]:
            if weekly_flight_time > self.hard_rules["max_flight_time_per_week"]:
                violations["weekly_flight_time_exceeded"] = True
        
        # Monthly flight time
        if self.hard_rules["max_flight_time_per_month"]:
            if monthly_flight_time > self.hard_rules["max_flight_time_per_month"]:
                violations["monthly_flight_time_exceeded"] = True
        
        # Night duty checks
        if self.is_night_duty(duty_start, duty_end):
            if self.hard_rules["max_night_duties_per_week"]:
                if weekly_night_duties >= self.hard_rules["max_night_duties_per_week"]:
                    violations["night_duty_limit_exceeded"] = True
        
        # Rank-specific hard rules
        rank_violations = self.check_rank_specific_hard_rules(crew_rank, duty_duration, consecutive_days, weekly_night_duties)
        violations.update(rank_violations)
        
        return violations
    
    def check_soft_rule_violations(self, duty_start: datetime, duty_end: datetime,
                                 crew_rank: str, consecutive_days: int,
                                 weekly_night_duties: int, crew_duty_count: int,
                                 avg_duty_count: float) -> Dict[str, float]:
        """Check for violations of soft rules (preferences/fairness) - return penalty scores"""
        penalties = {}
        
        duty_duration = duty_end - duty_start
        
        # Preference for shorter duty hours
        if duty_duration > self.soft_rules["preferred_max_duty_per_day"]:
            excess = (duty_duration - self.soft_rules["preferred_max_duty_per_day"]).total_seconds() / 3600
            penalties["long_duty_hours"] = excess * 0.5  # Penalty per hour over preferred limit
        
        # Preference for fewer consecutive days
        if self.soft_rules["preferred_max_consecutive_duty_days"]:
            if consecutive_days > self.soft_rules["preferred_max_consecutive_duty_days"]:
                excess = consecutive_days - self.soft_rules["preferred_max_consecutive_duty_days"]
                penalties["long_consecutive_days"] = excess * 1.0  # Penalty per day over preferred limit
        
        # Preference for fewer night duties
        if self.is_night_duty(duty_start, duty_end):
            if self.soft_rules["preferred_night_duties_per_week"]:
                if weekly_night_duties >= self.soft_rules["preferred_night_duties_per_week"]:
                    penalties["excessive_night_duties"] = 2.0  # Fixed penalty for exceeding preferred night duties
        
        # Fairness penalty - deviation from average duty count
        if avg_duty_count > 0:
            deviation = abs(crew_duty_count - avg_duty_count)
            penalties["fairness_deviation"] = deviation * self.soft_rules["fairness_weight"]
        
        return penalties
    
    def check_rank_specific_hard_rules(self, rank: str, duty_duration: timedelta,
                                     consecutive_days: int, night_duties: int) -> Dict[str, bool]:
        """Check rank-specific hard rules"""
        violations = {}
        
        # Captain and First Officer may have different limits
        if rank == "Captain":
            # Captains might have stricter limits
            if self.hard_rules["max_consecutive_duty_days"]:
                if consecutive_days > self.hard_rules["max_consecutive_duty_days"] - 1:
                    violations["consecutive_duty_days_exceeded"] = True
        elif rank == "FirstOfficer":
            # First Officers might have different limits
            if self.hard_rules["max_consecutive_duty_days"]:
                if consecutive_days > self.hard_rules["max_consecutive_duty_days"]:
                    violations["consecutive_duty_days_exceeded"] = True
        
        # Night duty limits are typically the same for both ranks
        if self.hard_rules["max_night_duties_per_week"]:
            if night_duties >= self.hard_rules["max_night_duties_per_week"]:
                violations["night_duty_limit_exceeded"] = True
                
        return violations
    
    def calculate_preference_score(self, crew_id: int, flight_date: datetime.date,
                                 dep_iata: str, arr_iata: str, flight_no: str,
                                 preferences: List[models.CrewPreference]) -> float:
        """Calculate preference satisfaction score for soft rules"""
        score = 0.0
        
        for pref in preferences:
            if pref.preference_type == "day_off" and pref.preference_value == flight_date.strftime("%A"):
                # Day off preference (negative score as it's a penalty to work on preferred day off)
                score -= pref.weight * 2.0
            elif pref.preference_type == "base" and pref.preference_value == dep_iata:
                # Base preference (positive score as it's a bonus)
                score += pref.weight * 1.5
            elif pref.preference_type == "destination" and pref.preference_value == arr_iata:
                # Destination preference (positive score as it's a bonus)
                score += pref.weight * 1.0
            elif pref.preference_type == "flight_no" and pref.preference_value == flight_no:
                # Specific flight number preference (positive score as it's a bonus)
                score += pref.weight * 2.5
            elif pref.preference_type == "weekend_off" and flight_date.weekday() >= 5:
                # Weekend off preference (negative score as it's a penalty to work on weekend)
                score -= pref.weight * 1.5
            elif pref.preference_type == "night_off" and self.is_night_duty_slot(dep_iata, arr_iata):
                # Night off preference (negative score as it's a penalty to work night flights)
                score -= pref.weight * 1.0
        
        return score
    
    def is_night_duty(self, start: datetime, end: datetime) -> bool:
        """Check if a duty period is considered a night duty (22:00-06:00)"""
        # Check if duty starts or ends during night hours
        night_start = start.replace(hour=22, minute=0, second=0, microsecond=0)
        night_end = start.replace(hour=6, minute=0, second=0, microsecond=0)
        
        # Handle overnight duties
        if start.hour >= 22 or start.hour < 6:
            return True
        if end.hour >= 22 or end.hour < 6:
            return True
        # Check if duty crosses midnight during night hours
        if start < night_start and end > night_end and night_end > night_start:
            return True
        return False
    
    def is_night_duty_slot(self, dep_iata: str, arr_iata: str) -> bool:
        """Check if a flight slot is typically a night flight (simplified)"""
        # This would be more complex in a real implementation
        # For now, we'll assume night flights based on departure/arrival airports
        night_airports = ["DEL", "BLR", "HYD", "BOM", "MAA"]  # All major airports in India
        # Simplified logic - in reality this would check actual flight times
        return True  # Placeholder
    
    def calculate_total_penalty(self, hard_violations: Dict[str, bool], 
                              soft_penalties: Dict[str, float]) -> Tuple[float, bool]:
        """Calculate total penalty and check if roster is valid (no hard violations)"""
        # Hard violations make roster invalid
        is_valid = len(hard_violations) == 0
        
        # Soft penalties are additive
        total_soft_penalty = sum(soft_penalties.values())
        
        # Hard violations have a very high penalty
        hard_penalty = len(hard_violations) * 1000.0
        
        total_penalty = hard_penalty + total_soft_penalty
        
        return total_penalty, is_valid
    
    def get_rule_categories(self) -> Dict[str, List[str]]:
        """Get categorized rules for display/analysis"""
        return {
            "hard_rules": [
                "Max duty hours per day",
                "Min rest hours after duty",
                "Max Flight Duty Period (FDP)",
                "Max duty hours per week",
                "Max duty hours per month",
                "Max consecutive duty days",
                "Min rest hours between duties",
                "Max night duties per week",
                "Min rest hours after night duty",
                "Max extended FDP hours",
                "Max flight time per day",
                "Max flight time per week",
                "Max flight time per month",
                "Crew qualification requirements",
                "No overlapping flights for same crew",
                "Correct crew composition per flight"
            ],
            "soft_rules": [
                "Preferred max duty hours per day",
                "Preferred max consecutive duty days",
                "Preferred rest hours after duty",
                "Preferred night duties per week",
                "Crew preference satisfaction",
                "Fairness in duty distribution",
                "Balance night vs day duties",
                "Balance weekend vs weekday assignments",
                "Minimize standby crew",
                "Minimize deadhead flights",
                "Historical stability",
                "Cost optimization"
            ]
        }