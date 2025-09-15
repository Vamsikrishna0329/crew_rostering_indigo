"""
Analytics API for crew rostering.
This module provides endpoints for predictive analytics and data-driven decision making.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.storage.db import SessionLocal
from app.schemas.roster import GenerateRosterRequest
from app.analytics import (
    analyze_crew_patterns,
    predict_crew_availability,
    predict_crew_performance,
    identify_risk_patterns
)
from datetime import date
from typing import Dict, Any

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/patterns/crew")
def get_crew_patterns(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Analyze crew patterns using clustering and other ML techniques.
    
    Returns:
        Dictionary containing pattern analysis results
    """
    try:
        result = analyze_crew_patterns(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing crew patterns: {str(e)}")

@router.get("/predict/availability/{crew_id}/{prediction_date}")
def get_crew_availability_prediction(
    crew_id: int, 
    prediction_date: date, 
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Predict crew availability for a specific date.
    
    Args:
        crew_id: ID of the crew member
        prediction_date: Date for which to predict availability
        
    Returns:
        Dictionary containing availability prediction
    """
    try:
        result = predict_crew_availability(db, crew_id, prediction_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting crew availability: {str(e)}")

@router.get("/predict/performance")
def get_crew_performance_predictions(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Predict crew performance based on historical data.
    
    Returns:
        Dictionary containing performance predictions
    """
    try:
        result = predict_crew_performance(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting crew performance: {str(e)}")

@router.get("/risks")
def get_risk_patterns(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Identify risk patterns in crew scheduling that could lead to disruptions.
    
    Returns:
        Dictionary containing identified risks
    """
    try:
        result = identify_risk_patterns(db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying risk patterns: {str(e)}")