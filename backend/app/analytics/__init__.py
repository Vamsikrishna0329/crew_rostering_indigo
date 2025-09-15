"""
Analytics package for crew rostering.
This package contains modules for predictive analytics and data-driven decision making.
"""

# Import key functions for easier access
from .predictive_analytics import (
    analyze_crew_patterns,
    predict_crew_availability,
    predict_crew_performance,
    identify_risk_patterns
)

__all__ = [
    "analyze_crew_patterns",
    "predict_crew_availability",
    "predict_crew_performance",
    "identify_risk_patterns"
]