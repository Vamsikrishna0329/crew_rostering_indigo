
from sqlalchemy import Column, Integer, BigInteger, Text, Date, ForeignKey, Numeric
from sqlalchemy.dialects.sqlite import DATETIME as TIMESTAMP
from app.storage.db import Base
class BaseAirport(Base):
    __tablename__ = "base_airport"
    iata = Column(Text, primary_key=True)
    city = Column(Text, nullable=False)
    tz = Column(Text, nullable=False)
class AircraftType(Base):
    __tablename__ = "aircraft_type"
    code = Column(Text, primary_key=True)
    description = Column(Text)
class Crew(Base):
    __tablename__ = "crew"
    crew_id = Column(BigInteger, primary_key=True)
    emp_code = Column(Text, unique=True, nullable=False)
    name = Column(Text, nullable=False)
    rank = Column(Text, nullable=False)
    base_iata = Column(ForeignKey("base_airport.iata"), nullable=False)
    status = Column(Text, nullable=False)
class CrewQualification(Base):
    __tablename__ = "crew_qualification"
    crew_id = Column(ForeignKey("crew.crew_id", ondelete="CASCADE"), primary_key=True)
    aircraft_code = Column(ForeignKey("aircraft_type.code"), primary_key=True)
    qualified_on = Column(Date, nullable=False)
    expires_on = Column(Date)

class CrewPreference(Base):
    __tablename__ = "crew_preference"
    crew_id = Column(ForeignKey("crew.crew_id", ondelete="CASCADE"), primary_key=True)
    preference_type = Column(Text, primary_key=True)  # 'day_off', 'base', 'sector', etc.
    preference_value = Column(Text, primary_key=True)  # specific day, base, sector, etc.
    weight = Column(Integer, nullable=False, default=1)  # preference strength (1-10)
    valid_from = Column(Date)
    valid_to = Column(Date)

class CrewAvailability(Base):
    __tablename__ = "crew_availability"
    crew_id = Column(ForeignKey("crew.crew_id", ondelete="CASCADE"), primary_key=True)
    availability_type = Column(Text, primary_key=True)  # 'leave', 'medical', 'training', etc.
    reason = Column(Text)  # specific reason for unavailability
    unavailable_from = Column(Date, nullable=False)
    unavailable_to = Column(Date, nullable=False)
    status = Column(Text, nullable=False, default="pending")  # pending, approved, rejected
    requested_on = Column(Date, nullable=False)
    approved_on = Column(Date)
    approved_by = Column(Text)

class DisruptionRecord(Base):
    __tablename__ = "disruption_record"
    disruption_id = Column(BigInteger, primary_key=True)
    flight_no = Column(Text, nullable=True)
    disruption_type = Column(Text, nullable=False)  # delay, cancellation, crew_unavailability
    disruption_date = Column(Date, nullable=False)
    impact_duration = Column(Integer)  # in minutes for delays
    crew_id = Column(ForeignKey("crew.crew_id"), nullable=True)  # for crew unavailability
    reason = Column(Text)
    resolution = Column(Text)
    recorded_at = Column(TIMESTAMP(timezone=False), nullable=False)
    resolved_at = Column(TIMESTAMP(timezone=False))

class Flight(Base):
    __tablename__ = "flight"
    flight_id = Column(BigInteger, primary_key=True)
    flight_no = Column(Text, nullable=False)
    flight_date = Column(Date, nullable=False)
    dep_iata = Column(ForeignKey("base_airport.iata"), nullable=False)
    arr_iata = Column(ForeignKey("base_airport.iata"), nullable=False)
    sched_dep_utc = Column(TIMESTAMP(timezone=False), nullable=False)
    sched_arr_utc = Column(TIMESTAMP(timezone=False), nullable=False)
    aircraft_code = Column(ForeignKey("aircraft_type.code"), nullable=False)
class DutyPeriod(Base):
    __tablename__ = "duty_period"
    duty_id = Column(BigInteger, primary_key=True)
    crew_id = Column(ForeignKey("crew.crew_id", ondelete="CASCADE"), nullable=False)
    duty_start_utc = Column(TIMESTAMP(timezone=False), nullable=False)
    duty_end_utc = Column(TIMESTAMP(timezone=False), nullable=False)
    base_iata = Column(ForeignKey("base_airport.iata"), nullable=False)
class DutyFlight(Base):
    __tablename__ = "duty_flight"
    duty_id = Column(ForeignKey("duty_period.duty_id", ondelete="CASCADE"), primary_key=True)
    flight_id = Column(ForeignKey("flight.flight_id", ondelete="CASCADE"), primary_key=True)
    leg_seq = Column(Integer, nullable=False)
class DGCAConstraints(Base):
    __tablename__ = "dgca_constraints"
    version = Column(Text, primary_key=True)
    # Basic duty/rest constraints
    max_duty_hours_per_day = Column(Numeric, nullable=False)
    min_rest_hours_after_duty = Column(Numeric, nullable=False)
    max_fdp_hours = Column(Numeric, nullable=False)
    
    # Extended DGCA constraints
    max_duty_hours_per_week = Column(Numeric, nullable=True)
    max_duty_hours_per_month = Column(Numeric, nullable=True)
    max_consecutive_duty_days = Column(Integer, nullable=True)
    min_rest_hours_between_duties = Column(Numeric, nullable=True)
    max_night_duties_per_week = Column(Integer, nullable=True)
    min_rest_hours_after_night_duty = Column(Numeric, nullable=True)
    max_extended_fdp_hours = Column(Numeric, nullable=True)
    max_flight_time_per_day = Column(Numeric, nullable=True)
    max_flight_time_per_week = Column(Numeric, nullable=True)
    max_flight_time_per_month = Column(Numeric, nullable=True)
    notes = Column(Text)
