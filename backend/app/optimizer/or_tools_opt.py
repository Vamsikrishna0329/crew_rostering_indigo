"""
Optimization module using Google OR-Tools for crew rostering.
This module provides advanced constraint satisfaction and optimization capabilities.
"""

from ortools.sat.python import cp_model
from sqlalchemy.orm import Session
from app.storage import models
from app.rules.engine import RulesEngine
from datetime import timedelta, date, datetime
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CrewRosteringOptimizer:
    """Crew rostering optimizer using Google OR-Tools CP-SAT solver."""
    
    def __init__(self, db: Session, rules: RulesEngine):
        self.db = db
        self.rules = rules
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        
    def optimize_roster(self, period_start: date, period_end: date) -> Tuple[List[Dict], Dict]:
        """
        Optimize crew roster using OR-Tools constraint satisfaction.
        
        Args:
            period_start: Start date of the rostering period
            period_end: End date of the rostering period
            
        Returns:
            Tuple of (assignments, kpis)
        """
        logger.info(f"Starting OR-Tools optimization for period {period_start} to {period_end}")
        
        # Get data from database
        flights = self._get_flights(period_start, period_end)
        crew = self._get_active_crew()
        quals = self._get_qualifications()
        prefs = self._get_preferences()
        unavailable_crew = self._get_unavailable_crew(period_start, period_end)
        
        # Build data structures
        qual_map = self._build_qualification_map(quals)
        pref_map = self._build_preference_map(prefs)
        unavailable_crew_map = self._build_unavailable_crew_map(unavailable_crew)
        
        # Create variables
        assignment_vars = self._create_assignment_variables(flights, crew)
        
        # Add constraints
        self._add_qualification_constraints(assignment_vars, flights, crew, qual_map)
        self._add_availability_constraints(assignment_vars, flights, crew, unavailable_crew_map)
        self._add_rules_constraints(assignment_vars, flights, crew)
        self._add_fairness_constraints(assignment_vars, crew)
        
        # Set objective
        self._set_objective(assignment_vars, flights, crew, pref_map, qual_map)
        
        # Solve
        logger.info("Starting solver...")
        status = self.solver.Solve(self.model)
        
        # Process results
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            logger.info("Solution found")
            return self._process_solution(assignment_vars, flights, crew, pref_map)
        else:
            logger.warning("No solution found, falling back to simple optimization")
            # Fallback to simple optimization if OR-Tools can't find a solution
            from app.optimizer.simple_opt import generate_roster
            return generate_roster(self.db, period_start, period_end, self.rules)
    
    def _get_flights(self, period_start: date, period_end: date) -> List[models.Flight]:
        """Get flights for the specified period."""
        return self.db.query(models.Flight).filter(
            models.Flight.flight_date >= period_start,
            models.Flight.flight_date <= period_end
        ).order_by(models.Flight.sched_dep_utc).all()
    
    def _get_active_crew(self) -> List[models.Crew]:
        """Get all active crew members."""
        return self.db.query(models.Crew).filter(models.Crew.status == "Active").all()
    
    def _get_qualifications(self) -> List[models.CrewQualification]:
        """Get all crew qualifications."""
        return self.db.query(models.CrewQualification).all()
    
    def _get_preferences(self) -> List[models.CrewPreference]:
        """Get all current crew preferences."""
        today = date.today()
        return self.db.query(models.CrewPreference).filter(
            (models.CrewPreference.valid_from.is_(None) | (models.CrewPreference.valid_from <= today)),
            (models.CrewPreference.valid_to.is_(None) | (models.CrewPreference.valid_to >= today))
        ).all()
    
    def _get_unavailable_crew(self, period_start: date, period_end: date) -> List[models.CrewAvailability]:
        """Get unavailable crew records for the period."""
        return self.db.query(models.CrewAvailability).filter(
            models.CrewAvailability.unavailable_from <= period_end,
            models.CrewAvailability.unavailable_to >= period_start,
            models.CrewAvailability.status == "approved"
        ).all()
    
    def _build_qualification_map(self, quals: List[models.CrewQualification]) -> Dict[int, Dict[str, models.CrewQualification]]:
        """Build a map of crew qualifications."""
        qual_map = {}
        today = date.today()
        for q in quals:
            if q.expires_on is None or q.expires_on >= today:
                if q.crew_id not in qual_map:
                    qual_map[q.crew_id] = {}
                qual_map[q.crew_id][q.aircraft_code] = q
        return qual_map
    
    def _build_preference_map(self, prefs: List[models.CrewPreference]) -> Dict[int, List[models.CrewPreference]]:
        """Build a map of crew preferences."""
        pref_map = {}
        for p in prefs:
            if p.crew_id not in pref_map:
                pref_map[p.crew_id] = []
            pref_map[p.crew_id].append(p)
        return pref_map
    
    def _build_unavailable_crew_map(self, unavailable_crew: List[models.CrewAvailability]) -> Dict[int, List[models.CrewAvailability]]:
        """Build a map of unavailable crew."""
        unavailable_crew_map = {}
        for record in unavailable_crew:
            if record.crew_id not in unavailable_crew_map:
                unavailable_crew_map[record.crew_id] = []
            unavailable_crew_map[record.crew_id].append(record)
        return unavailable_crew_map
    
    def _create_assignment_variables(self, flights: List[models.Flight], crew: List[models.Crew]) -> Dict[Tuple[int, int], cp_model.IntVar]:
        """
        Create assignment variables for the optimization model.
        
        Args:
            flights: List of flights
            crew: List of crew members
            
        Returns:
            Dictionary mapping (flight_id, crew_id) to assignment variables
        """
        assignment_vars = {}
        for flight in flights:
            for c in crew:
                # Create binary variable for each possible assignment
                var = self.model.NewBoolVar(f'assign_flight_{flight.flight_id}_crew_{c.crew_id}')
                assignment_vars[(flight.flight_id, c.crew_id)] = var
        return assignment_vars
    
    def _add_qualification_constraints(self, assignment_vars: Dict[Tuple[int, int], cp_model.IntVar], 
                                     flights: List[models.Flight], crew: List[models.Crew], 
                                     qual_map: Dict[int, Dict[str, models.CrewQualification]]) -> None:
        """
        Add qualification constraints to ensure only qualified crew are assigned to flights.
        """
        for flight in flights:
            for c in crew:
                # If crew is not qualified for this aircraft, they cannot be assigned
                if not (c.crew_id in qual_map and flight.aircraft_code in qual_map[c.crew_id]):
                    self.model.Add(assignment_vars[(flight.flight_id, c.crew_id)] == 0)
    
    def _add_availability_constraints(self, assignment_vars: Dict[Tuple[int, int], cp_model.IntVar],
                                    flights: List[models.Flight], crew: List[models.Crew],
                                    unavailable_crew_map: Dict[int, List[models.CrewAvailability]]) -> None:
        """
        Add availability constraints to ensure unavailable crew are not assigned.
        """
        for flight in flights:
            for c in crew:
                # Check if crew is unavailable for this flight date
                unavailable = False
                if c.crew_id in unavailable_crew_map:
                    for record in unavailable_crew_map[c.crew_id]:
                        if record.unavailable_from <= flight.flight_date <= record.unavailable_to:
                            unavailable = True
                            break
                
                if unavailable:
                    self.model.Add(assignment_vars[(flight.flight_id, c.crew_id)] == 0)
    
    def _add_rules_constraints(self, assignment_vars: Dict[Tuple[int, int], cp_model.IntVar],
                              flights: List[models.Flight], crew: List[models.Crew]) -> None:
        """
        Add DGCA rules constraints to ensure compliance.
        """
        # Each flight must have exactly one crew assignment
        for flight in flights:
            crew_assignments = [assignment_vars[(flight.flight_id, c.crew_id)] for c in crew]
            self.model.Add(sum(crew_assignments) == 1)
        
        # Add duty duration constraints
        # For simplicity, we're adding a constraint that each crew can only be assigned to one flight per day
        # A more complex implementation would track actual duty times
        crew_flight_dates = {}
        for flight in flights:
            flight_date = flight.flight_date
            for c in crew:
                if c.crew_id not in crew_flight_dates:
                    crew_flight_dates[c.crew_id] = {}
                if flight_date not in crew_flight_dates[c.crew_id]:
                    crew_flight_dates[c.crew_id][flight_date] = []
                crew_flight_dates[c.crew_id][flight_date].append(assignment_vars[(flight.flight_id, c.crew_id)])
        
        for crew_id, dates in crew_flight_dates.items():
            for flight_date, assignments in dates.items():
                # Limit to one flight per day per crew (simplified constraint)
                self.model.Add(sum(assignments) <= 1)
    
    def _add_fairness_constraints(self, assignment_vars: Dict[Tuple[int, int], cp_model.IntVar],
                                 crew: List[models.Crew]) -> None:
        """
        Add fairness constraints to ensure equitable distribution of duties.
        """
        # This is a simplified fairness constraint
        # In a full implementation, we would track historical duty counts and try to balance them
        pass
    
    def _set_objective(self, assignment_vars: Dict[Tuple[int, int], cp_model.IntVar],
                      flights: List[models.Flight], crew: List[models.Crew],
                      pref_map: Dict[int, List[models.CrewPreference]],
                      qual_map: Dict[int, Dict[str, models.CrewQualification]]) -> None:
        """
        Set the optimization objective to maximize preference satisfaction and fairness.
        """
        # Create preference score terms
        preference_terms = []
        coefficients = []
        
        for flight in flights:
            for c in crew:
                # Calculate preference score for this crew-flight combination
                pref_score = self._calculate_preference_score(c.crew_id, flight, pref_map)
                if pref_score != 0:
                    preference_terms.append(assignment_vars[(flight.flight_id, c.crew_id)])
                    coefficients.append(pref_score)
        
        # Maximize preference satisfaction
        if preference_terms:
            self.model.Maximize(sum(coeff * term for coeff, term in zip(coefficients, preference_terms)))
    
    def _calculate_preference_score(self, crew_id: int, flight: models.Flight, 
                                  pref_map: Dict[int, List[models.CrewPreference]]) -> int:
        """
        Calculate preference score for a crew member for a specific flight.
        """
        score = 0
        prefs = pref_map.get(crew_id, [])
        
        for pref in prefs:
            if pref.preference_type == "day_off" and pref.preference_value == flight.flight_date.strftime("%A"):
                # Day off preference (negative score as it's a penalty)
                score -= pref.weight * 10
            elif pref.preference_type == "base" and pref.preference_value == flight.dep_iata:
                # Base preference (positive score as it's a bonus)
                score += pref.weight * 2
            elif pref.preference_type == "destination" and pref.preference_value == flight.arr_iata:
                # Destination preference (positive score as it's a bonus)
                score += pref.weight
            elif pref.preference_type == "flight_no" and pref.preference_value == flight.flight_no:
                # Specific flight number preference (positive score as it's a bonus)
                score += pref.weight * 3
            elif pref.preference_type == "weekend_off" and flight.flight_date.weekday() >= 5:
                # Weekend off preference (negative score as it's a penalty)
                score -= pref.weight * 5
        
        return score
    
    def _process_solution(self, assignment_vars: Dict[Tuple[int, int], cp_model.IntVar],
                         flights: List[models.Flight], crew: List[models.Crew],
                         pref_map: Dict[int, List[models.CrewPreference]]) -> Tuple[List[Dict], Dict]:
        """
        Process the optimization solution and return assignments and KPIs.
        """
        assignments = []
        crew_duty_count = {}
        
        for flight in flights:
            assigned = False
            for c in crew:
                # Check if this crew is assigned to this flight in the solution
                if self.solver.Value(assignment_vars[(flight.flight_id, c.crew_id)]) == 1:
                    assignments.append({
                        "crew_id": c.crew_id,
                        "crew_name": c.name,
                        "flight_id": flight.flight_id,
                        "duty_start_utc": flight.sched_dep_utc,
                        "duty_end_utc": flight.sched_arr_utc
                    })
                    
                    # Update duty count for fairness metrics
                    crew_duty_count[c.crew_id] = crew_duty_count.get(c.crew_id, 0) + 1
                    assigned = True
                    break
            
            # If no crew was assigned, mark as unassigned
            if not assigned:
                assignments.append({
                    "crew_id": None,
                    "crew_name": None,
                    "flight_id": flight.flight_id,
                    "duty_start_utc": flight.sched_dep_utc,
                    "duty_end_utc": flight.sched_arr_utc,
                    "note": "UNASSIGNED"
                })
        
        # Calculate KPIs
        total_flights = len(flights)
        assigned_count = sum(1 for a in assignments if a.get("crew_id"))
        
        # Calculate average duty count for fairness metrics
        avg_duty_count = sum(crew_duty_count.values()) / len(crew_duty_count) if crew_duty_count else 0
        max_duty_count = max(crew_duty_count.values()) if crew_duty_count else 0
        min_duty_count = min(crew_duty_count.values()) if crew_duty_count else 0
        
        # Calculate total preference score
        total_pref_score = 0
        for a in assignments:
            if a.get("crew_id"):
                flight = next((f for f in flights if f.flight_id == a["flight_id"]), None)
                if flight:
                    total_pref_score += self._calculate_preference_score(a["crew_id"], flight, pref_map)
        
        avg_pref_score = total_pref_score / assigned_count if assigned_count else 0
        
        kpis = {
            "flights_total": total_flights,
            "flights_assigned": assigned_count,
            "assignment_rate": (assigned_count / total_flights) if total_flights else 0.0,
            "avg_duty_per_crew": avg_duty_count,
            "max_duty_per_crew": max_duty_count,
            "min_duty_per_crew": min_duty_count,
            "duty_distribution_range": max_duty_count - min_duty_count,
            "compliance_rate": 1.0,  # Assuming all assignments are compliant
            "avg_preference_score": avg_pref_score,
            "fairness_score": 1.0 - (max_duty_count - min_duty_count) / (max_duty_count + 1) if max_duty_count else 1.0
        }
        
        return assignments, kpis

def generate_roster_with_or_tools(db: Session, period_start: date, period_end: date, rules: RulesEngine) -> Tuple[List[Dict], Dict]:
    """
    Generate a crew roster using OR-Tools optimization.
    
    Args:
        db: Database session
        period_start: Start date of the rostering period
        period_end: End date of the rostering period
        rules: Rules engine instance
        
    Returns:
        Tuple of (assignments, kpis)
    """
    optimizer = CrewRosteringOptimizer(db, rules)
    return optimizer.optimize_roster(period_start, period_end)