# AI-Powered Crew Rostering Database Schema

## Overview
This document describes the complete database schema for the AI-powered crew rostering system for IndiGo. The database has been enhanced to support all the features required for the POC, including comprehensive DGCA compliance, crew qualification management, preference handling, and disruption management.

## Database Structure

### 1. Base Airport Table (`base_airport`)
Stores information about airport bases where crew members are stationed.

**Columns:**
- `iata` (TEXT, PRIMARY KEY) - IATA code of the airport
- `city` (TEXT, NOT NULL) - City name
- `tz` (TEXT, NOT NULL) - Timezone

**Sample Data:**
- DEL: Delhi, Asia/Kolkata
- BLR: Bengaluru, Asia/Kolkata
- HYD: Hyderabad, Asia/Kolkata
- BOM: Mumbai, Asia/Kolkata
- MAA: Chennai, Asia/Kolkata

### 2. Aircraft Type Table (`aircraft_type`)
Stores information about different aircraft types.

**Columns:**
- `code` (TEXT, PRIMARY KEY) - Aircraft type code
- `description` (TEXT) - Description of the aircraft type

**Sample Data:**
- A320: Airbus A320
- A321: Airbus A321

### 3. Crew Table (`crew`)
Stores information about crew members.

**Columns:**
- `crew_id` (INTEGER, PRIMARY KEY) - Unique identifier for the crew member
- `emp_code` (TEXT, UNIQUE, NOT NULL) - Employee code
- `name` (TEXT, NOT NULL) - Crew member name
- `rank` (TEXT, NOT NULL) - Rank (Captain or FirstOfficer)
- `base_iata` (TEXT, NOT NULL) - Base airport IATA code (foreign key to base_airport)
- `status` (TEXT, NOT NULL) - Employment status (Active, Inactive, etc.)

### 4. Crew Qualification Table (`crew_qualification`)
Stores information about crew qualifications for different aircraft types.

**Columns:**
- `crew_id` (INTEGER, PRIMARY KEY) - Crew member ID (foreign key to crew)
- `aircraft_code` (TEXT, PRIMARY KEY) - Aircraft type code (foreign key to aircraft_type)
- `qualified_on` (DATE, NOT NULL) - Date when qualification was obtained
- `expires_on` (DATE) - Date when qualification expires

### 5. Flight Table (`flight`)
Stores information about scheduled flights.

**Columns:**
- `flight_id` (INTEGER, PRIMARY KEY) - Unique identifier for the flight
- `flight_no` (TEXT, NOT NULL) - Flight number
- `flight_date` (DATE, NOT NULL) - Date of the flight
- `dep_iata` (TEXT, NOT NULL) - Departure airport IATA code (foreign key to base_airport)
- `arr_iata` (TEXT, NOT NULL) - Arrival airport IATA code (foreign key to base_airport)
- `sched_dep_utc` (TEXT, NOT NULL) - Scheduled departure time (UTC)
- `sched_arr_utc` (TEXT, NOT NULL) - Scheduled arrival time (UTC)
- `aircraft_code` (TEXT, NOT NULL) - Aircraft type code (foreign key to aircraft_type)

### 6. Duty Period Table (`duty_period`)
Stores information about crew duty periods.

**Columns:**
- `duty_id` (INTEGER, PRIMARY KEY) - Unique identifier for the duty period
- `crew_id` (INTEGER, NOT NULL) - Crew member ID (foreign key to crew)
- `duty_start_utc` (TEXT, NOT NULL) - Duty start time (UTC)
- `duty_end_utc` (TEXT, NOT NULL) - Duty end time (UTC)
- `base_iata` (TEXT, NOT NULL) - Base airport IATA code (foreign key to base_airport)

### 7. Duty Flight Table (`duty_flight`)
Links duty periods to specific flights.

**Columns:**
- `duty_id` (INTEGER, PRIMARY KEY) - Duty period ID (foreign key to duty_period)
- `flight_id` (INTEGER, PRIMARY KEY) - Flight ID (foreign key to flight)
- `leg_seq` (INTEGER, NOT NULL) - Sequence number of the flight leg in the duty

### 8. DGCA Constraints Table (`dgca_constraints`)
Stores DGCA regulatory constraints for compliance checking.

**Columns:**
- `version` (TEXT, PRIMARY KEY) - Constraint set version
- `max_duty_hours_per_day` (REAL, NOT NULL) - Maximum duty hours per day
- `min_rest_hours_after_duty` (REAL, NOT NULL) - Minimum rest hours after duty
- `max_fdp_hours` (REAL, NOT NULL) - Maximum Flight Duty Period hours
- `max_duty_hours_per_week` (REAL) - Maximum duty hours per week
- `max_duty_hours_per_month` (REAL) - Maximum duty hours per month
- `max_consecutive_duty_days` (INTEGER) - Maximum consecutive duty days
- `min_rest_hours_between_duties` (REAL) - Minimum rest hours between duties
- `max_night_duties_per_week` (INTEGER) - Maximum night duties per week
- `min_rest_hours_after_night_duty` (REAL) - Minimum rest hours after night duty
- `max_extended_fdp_hours` (REAL) - Maximum extended Flight Duty Period hours
- `max_flight_time_per_day` (REAL) - Maximum flight time per day
- `max_flight_time_per_week` (REAL) - Maximum flight time per week
- `max_flight_time_per_month` (REAL) - Maximum flight time per month
- `notes` (TEXT) - Additional notes

### 9. Crew Preference Table (`crew_preference`)
Stores crew preferences for scheduling.

**Columns:**
- `crew_id` (INTEGER, PRIMARY KEY) - Crew member ID (foreign key to crew)
- `preference_type` (TEXT, PRIMARY KEY) - Type of preference (day_off, base, sector, etc.)
- `preference_value` (TEXT, PRIMARY KEY) - Specific preference value
- `weight` (INTEGER, NOT NULL, DEFAULT 1) - Preference strength (1-10)
- `valid_from` (DATE) - Date when preference becomes valid
- `valid_to` (DATE) - Date when preference expires

## Database Statistics

The complete database contains:
- **5 airports** across major Indian cities
- **2 aircraft types** (A320, A321)
- **1,000 crew members** with real names, various ranks and bases
- **1,316 crew qualifications** with expiry dates
- **20 crew preferences** for the first 10 crew members
- **13,500 flights** scheduled over 30 days
- **500 duty periods** linking crew members to flights
- **500 duty flights** linking duty periods to specific flights
- **1 set of DGCA constraints** with all enhanced regulatory parameters

## Key Features

### Enhanced DGCA Compliance
The database includes comprehensive DGCA constraints that support:
- Daily, weekly, and monthly duty hour limits
- Consecutive duty day restrictions
- Night duty limitations
- Extended FDP allowances
- Flight time restrictions

### Crew Qualification Management
The qualification system tracks:
- Aircraft type certifications
- Qualification validity periods
- Expiry dates for compliance

### Preference Handling
The preference system supports:
- Day off preferences (Sunday, Saturday, etc.)
- Base location preferences
- Weighted preference scoring
- Validity periods for preferences

### Disruption Management
The database structure supports:
- Flight scheduling and rescheduling
- Duty period tracking
- Crew assignment history

## Data Relationships

The database schema implements the following key relationships:
- Crew members are assigned to base airports
- Crew members have qualifications for specific aircraft types
- Flights are associated with specific aircraft types
- Duty periods link crew members to flights
- Preferences are associated with crew members
- All constraints are versioned for regulatory compliance

This comprehensive database schema provides a solid foundation for the AI-powered crew rostering system, supporting all the enhanced features implemented for the IndiGo POC.