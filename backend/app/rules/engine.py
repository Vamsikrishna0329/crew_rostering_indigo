
from datetime import timedelta, datetime
from typing import Optional, List, Dict

class RulesEngine:
    def __init__(
        self,
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
        max_flight_time_per_month: Optional[float] = None
    ):
        # Basic duty/rest constraints
        self.max_duty_per_day = timedelta(hours=max_duty_hours_per_day)
        self.min_rest_after_duty = timedelta(hours=min_rest_hours_after_duty)
        self.max_fdp = timedelta(hours=max_fdp_hours)
        
        # Extended DGCA constraints
        self.max_duty_per_week = timedelta(hours=max_duty_hours_per_week) if max_duty_hours_per_week else None
        self.max_duty_per_month = timedelta(hours=max_duty_hours_per_month) if max_duty_hours_per_month else None
        self.max_consecutive_duty_days = max_consecutive_duty_days
        self.min_rest_between_duties = timedelta(hours=min_rest_hours_between_duties) if min_rest_hours_between_duties else None
        self.max_night_duties_per_week = max_night_duties_per_week
        self.min_rest_after_night_duty = timedelta(hours=min_rest_hours_after_night_duty) if min_rest_hours_after_night_duty else None
        self.max_extended_fdp = timedelta(hours=max_extended_fdp_hours) if max_extended_fdp_hours else None
        self.max_flight_time_per_day = timedelta(hours=max_flight_time_per_day) if max_flight_time_per_day else None
        self.max_flight_time_per_week = timedelta(hours=max_flight_time_per_week) if max_flight_time_per_week else None
        self.max_flight_time_per_month = timedelta(hours=max_flight_time_per_month) if max_flight_time_per_month else None
    
    def duty_duration_ok(self, start: datetime, end: datetime) -> bool:
        """Check if duty duration is within limits"""
        duty_duration = end - start
        if duty_duration > self.max_duty_per_day:
            return False
        if duty_duration > self.max_fdp:
            return False
        return True
    
    def rest_ok(self, last_end: Optional[datetime], new_start: datetime) -> bool:
        """Check if rest period between duties is sufficient"""
        if last_end is None:
            return True
        rest_duration = new_start - last_end
        if self.min_rest_between_duties:
            return rest_duration >= self.min_rest_between_duties
        return rest_duration >= self.min_rest_after_duty
    
    def weekly_duty_ok(self, weekly_duties: List[timedelta]) -> bool:
        """Check if weekly duty hours are within limits"""
        if not self.max_duty_per_week:
            return True
        total_weekly_duty = sum(weekly_duties, timedelta())
        return total_weekly_duty <= self.max_duty_per_week
    
    def monthly_duty_ok(self, monthly_duties: List[timedelta]) -> bool:
        """Check if monthly duty hours are within limits"""
        if not self.max_duty_per_month:
            return True
        total_monthly_duty = sum(monthly_duties, timedelta())
        return total_monthly_duty <= self.max_duty_per_month
    
    def consecutive_duty_days_ok(self, consecutive_days: int) -> bool:
        """Check if consecutive duty days are within limits"""
        if not self.max_consecutive_duty_days:
            return True
        return consecutive_days <= self.max_consecutive_duty_days
    
    def night_duty_ok(self, weekly_night_duties: int) -> bool:
        """Check if weekly night duties are within limits"""
        if not self.max_night_duties_per_week:
            return True
        return weekly_night_duties <= self.max_night_duties_per_week
    
    def extended_fdp_ok(self, start: datetime, end: datetime, is_extended: bool = False) -> bool:
        """Check if FDP is within extended limits when applicable"""
        duty_duration = end - start
        if is_extended and self.max_extended_fdp:
            return duty_duration <= self.max_extended_fdp
        return duty_duration <= self.max_fdp
    
    def daily_flight_time_ok(self, flight_time: timedelta) -> bool:
        """Check if daily flight time is within limits"""
        if not self.max_flight_time_per_day:
            return True
        return flight_time <= self.max_flight_time_per_day
    
    def weekly_flight_time_ok(self, weekly_flight_time: timedelta) -> bool:
        """Check if weekly flight time is within limits"""
        if not self.max_flight_time_per_week:
            return True
        return weekly_flight_time <= self.max_flight_time_per_week
    
    def monthly_flight_time_ok(self, monthly_flight_time: timedelta) -> bool:
        """Check if monthly flight time is within limits"""
        if not self.max_flight_time_per_month:
            return True
        return monthly_flight_time <= self.max_flight_time_per_month
    
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
    
    def check_rank_specific_rules(self, rank: str, duty_duration: timedelta,
                                   consecutive_days: int, night_duties: int) -> Dict[str, bool]:
        """Check rank-specific DGCA rules"""
        violations = {}
        
        # Captain and First Officer may have different limits
        if rank == "Captain":
            # Captains might have stricter limits
            if self.max_consecutive_duty_days and consecutive_days > self.max_consecutive_duty_days - 1:
                violations["consecutive_duty_days"] = True
        elif rank == "FirstOfficer":
            # First Officers might have different limits
            if self.max_consecutive_duty_days and consecutive_days > self.max_consecutive_duty_days:
                violations["consecutive_duty_days"] = True
        
        # Night duty limits are typically the same for both ranks
        if self.max_night_duties_per_week and night_duties > self.max_night_duties_per_week:
            violations["night_duties_per_week"] = True
            
        return violations
    
    def calculate_duty_period_compliance(self, start: datetime, end: datetime,
                                          rank: str, consecutive_days: int,
                                          weekly_duties: List[timedelta],
                                          monthly_duties: List[timedelta],
                                          weekly_night_duties: int,
                                          weekly_flight_time: timedelta,
                                          monthly_flight_time: timedelta) -> Dict[str, bool]:
        """Comprehensive duty period compliance check"""
        violations = {}
        
        duty_duration = end - start
        
        # Basic duty duration checks
        if not self.duty_duration_ok(start, end):
            violations["duty_duration"] = True
        
        # Flight time checks
        if not self.daily_flight_time_ok(duty_duration):
            violations["daily_flight_time"] = True
            
        # Weekly duty checks
        if not self.weekly_duty_ok(weekly_duties):
            violations["weekly_duty"] = True
            
        # Monthly duty checks
        if not self.monthly_duty_ok(monthly_duties):
            violations["monthly_duty"] = True
            
        # Consecutive duty days
        if not self.consecutive_duty_days_ok(consecutive_days):
            violations["consecutive_duty_days"] = True
            
        # Weekly flight time
        if not self.weekly_flight_time_ok(weekly_flight_time):
            violations["weekly_flight_time"] = True
            
        # Monthly flight time
        if not self.monthly_flight_time_ok(monthly_flight_time):
            violations["monthly_flight_time"] = True
            
        # Night duty checks
        if self.is_night_duty(start, end):
            if not self.night_duty_ok(weekly_night_duties):
                violations["night_duty"] = True
        
        # Rank-specific rules
        rank_violations = self.check_rank_specific_rules(rank, duty_duration, consecutive_days, weekly_night_duties)
        violations.update(rank_violations)
        
        return violations
    
    def get_rest_period_for_extended_fdp(self, duty_duration: timedelta) -> timedelta:
        """Calculate required rest period based on duty duration for extended FDP"""
        hours = duty_duration.total_seconds() / 3600
        
        # DGCA rules for rest periods based on duty duration
        if hours <= 8:
            return timedelta(hours=10)  # Minimum rest
        elif hours <= 10:
            return timedelta(hours=12)
        elif hours <= 12:
            return timedelta(hours=14)
        else:
            return timedelta(hours=16)  # Extended rest for long duties
    
    def is_duty_extendable(self, start: datetime, end: datetime,
                            rank: str, consecutive_days: int) -> bool:
        """Check if a duty can be extended based on DGCA rules"""
        duty_duration = end - start
        
        # Only allow extension if within extended FDP limits
        if not self.extended_fdp_ok(start, end, is_extended=True):
            return False
            
        # Check consecutive days limit for extensions
        if self.max_consecutive_duty_days and consecutive_days >= self.max_consecutive_duty_days:
            return False
            
        # Captains may have different extension rules
        if rank == "Captain":
            # Captains might have stricter extension rules
            return duty_duration.total_seconds() / 3600 <= (self.max_extended_fdp.total_seconds() / 3600 - 1)
            
        return True
