"""
Optimizer package for crew rostering.
This package contains modules for optimization and constraint satisfaction.
"""

# Import key functions for easier access
from .simple_opt import generate_roster, propose_patch_for_delay, handle_flight_cancellation, handle_crew_unavailability
from .or_tools_opt import generate_roster_with_or_tools

__all__ = [
    "generate_roster",
    "propose_patch_for_delay",
    "handle_flight_cancellation",
    "handle_crew_unavailability",
    "generate_roster_with_or_tools"
]