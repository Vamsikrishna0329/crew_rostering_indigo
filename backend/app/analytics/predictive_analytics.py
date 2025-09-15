"""
Predictive analytics module using scikit-learn for crew rostering.
This module provides pattern analysis, predictive modeling, and data-driven decision making capabilities.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_squared_error
from sqlalchemy.orm import Session
from app.storage import models
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class CrewRosteringPredictor:
    """Crew rostering predictor using scikit-learn for pattern analysis and predictive modeling."""
    
    def __init__(self, db: Session):
        self.db = db
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def analyze_crew_patterns(self) -> Dict[str, Any]:
        """
        Analyze crew patterns using clustering and other ML techniques.
        
        Returns:
            Dictionary containing pattern analysis results
        """
        logger.info("Starting crew pattern analysis")
        
        # Get historical data
        duty_data = self._get_duty_history()
        crew_data = self._get_crew_data()
        
        if duty_data.empty:
            return {"error": "No historical duty data available"}
        
        # Perform clustering analysis
        clusters = self._perform_clustering(duty_data, crew_data)
        
        # Analyze preferences
        preference_analysis = self._analyze_preferences()
        
        # Analyze availability patterns
        availability_analysis = self._analyze_availability_patterns()
        
        return {
            "clustering_results": clusters,
            "preference_analysis": preference_analysis,
            "availability_analysis": availability_analysis,
            "analysis_date": datetime.now().isoformat()
        }
    
    def predict_crew_availability(self, crew_id: int, prediction_date: date) -> Dict[str, Any]:
        """
        Predict crew availability for a specific date.
        
        Args:
            crew_id: ID of the crew member
            prediction_date: Date for which to predict availability
            
        Returns:
            Dictionary containing availability prediction
        """
        logger.info(f"Predicting availability for crew {crew_id} on {prediction_date}")
        
        # Get historical availability data
        availability_data = self._get_crew_availability_history(crew_id)
        
        if availability_data.empty or len(availability_data) < 5:
            # Not enough data for reliable prediction, use simple heuristics
            return self._simple_availability_prediction(crew_id, prediction_date)
        
        # Train model and make prediction
        try:
            model = self._train_availability_model(availability_data)
            prediction = self._predict_availability(model, crew_id, prediction_date)
            return prediction
        except Exception as e:
            logger.error(f"Error in availability prediction: {e}")
            # Fallback to simple prediction
            return self._simple_availability_prediction(crew_id, prediction_date)
    
    def predict_crew_performance(self) -> Dict[str, Any]:
        """
        Predict crew performance based on historical data.
        
        Returns:
            Dictionary containing performance predictions
        """
        logger.info("Predicting crew performance")
        
        # Get historical performance data
        performance_data = self._get_performance_data()
        
        if performance_data.empty:
            return {"error": "No performance data available"}
        
        # Train performance prediction model
        model = self._train_performance_model(performance_data)
        
        # Make predictions for all active crew
        crew = self._get_active_crew()
        predictions = {}
        
        for c in crew:
            pred = self._predict_crew_performance(model, c.crew_id, performance_data)
            if pred:
                predictions[c.crew_id] = {
                    "crew_name": c.name,
                    "predicted_performance": pred,
                    "factors": self._get_performance_factors(c.crew_id, performance_data)
                }
        
        return {
            "predictions": predictions,
            "prediction_date": datetime.now().isoformat()
        }
    
    def identify_risk_patterns(self) -> Dict[str, Any]:
        """
        Identify risk patterns in crew scheduling that could lead to disruptions.
        
        Returns:
            Dictionary containing identified risks
        """
        logger.info("Identifying risk patterns")
        
        # Get historical disruption data
        disruption_data = self._get_disruption_history()
        
        if disruption_data.empty:
            return {"message": "No disruption data available"}
        
        # Identify patterns in disruptions
        disruption_patterns = self._analyze_disruption_patterns(disruption_data)
        
        # Identify crew at risk of burnout
        burnout_risks = self._identify_burnout_risks()
        
        # Identify scheduling conflicts
        scheduling_conflicts = self._identify_scheduling_conflicts()
        
        return {
            "disruption_patterns": disruption_patterns,
            "burnout_risks": burnout_risks,
            "scheduling_conflicts": scheduling_conflicts,
            "analysis_date": datetime.now().isoformat()
        }
    
    def _get_duty_history(self) -> pd.DataFrame:
        """Get historical duty data."""
        # In a real implementation, we would query the duty_period and duty_flight tables
        # For now, we'll simulate some data
        duties = self.db.query(models.DutyPeriod).all()
        
        if not duties:
            return pd.DataFrame()
        
        data = []
        for duty in duties:
            data.append({
                "duty_id": duty.duty_id,
                "crew_id": duty.crew_id,
                "duty_start": duty.duty_start_utc,
                "duty_end": duty.duty_end_utc,
                "duration": (duty.duty_end_utc - duty.duty_start_utc).total_seconds() / 3600.0,
                "day_of_week": duty.duty_start_utc.weekday(),
                "is_weekend": 1 if duty.duty_start_utc.weekday() >= 5 else 0,
                "month": duty.duty_start_utc.month
            })
        
        return pd.DataFrame(data)
    
    def _get_crew_data(self) -> pd.DataFrame:
        """Get crew data."""
        crew = self.db.query(models.Crew).all()
        
        if not crew:
            return pd.DataFrame()
        
        data = []
        for c in crew:
            data.append({
                "crew_id": c.crew_id,
                "rank": c.rank,
                "base_iata": c.base_iata,
                "status": c.status
            })
        
        return pd.DataFrame(data)
    
    def _perform_clustering(self, duty_data: pd.DataFrame, crew_data: pd.DataFrame) -> Dict[str, Any]:
        """Perform clustering analysis on crew duty patterns."""
        try:
            # Merge duty and crew data
            merged_data = duty_data.merge(crew_data, on="crew_id", how="left")
            
            # Prepare features for clustering
            features = ["duration", "day_of_week", "is_weekend", "month"]
            
            # Encode categorical variables
            if "rank" in merged_data.columns:
                le = LabelEncoder()
                merged_data["rank_encoded"] = le.fit_transform(merged_data["rank"].fillna("Unknown"))
                features.append("rank_encoded")
            
            # Select features for clustering
            X = merged_data[features].fillna(0)
            
            # Standardize features
            X_scaled = self.scaler.fit_transform(X)
            
            # Perform clustering
            kmeans = KMeans(n_clusters=min(5, len(X_scaled)//10), random_state=42)
            clusters = kmeans.fit_predict(X_scaled)
            
            # Add cluster labels to data
            merged_data["cluster"] = clusters
            
            # Calculate cluster statistics
            cluster_stats = {}
            for cluster_id in range(kmeans.n_clusters):
                cluster_data = merged_data[merged_data["cluster"] == cluster_id]
                cluster_stats[cluster_id] = {
                    "size": len(cluster_data),
                    "avg_duration": cluster_data["duration"].mean(),
                    "weekend_percentage": cluster_data["is_weekend"].mean() * 100,
                    "crew_ids": cluster_data["crew_id"].tolist()
                }
            
            return {
                "n_clusters": kmeans.n_clusters,
                "cluster_stats": cluster_stats,
                "inertia": kmeans.inertia_
            }
        except Exception as e:
            logger.error(f"Error in clustering: {e}")
            return {"error": f"Clustering failed: {str(e)}"}
    
    def _analyze_preferences(self) -> Dict[str, Any]:
        """Analyze crew preferences."""
        prefs = self.db.query(models.CrewPreference).all()
        
        if not prefs:
            return {"message": "No preference data available"}
        
        pref_data = []
        for p in prefs:
            pref_data.append({
                "crew_id": p.crew_id,
                "preference_type": p.preference_type,
                "preference_value": p.preference_value,
                "weight": p.weight
            })
        
        df = pd.DataFrame(pref_data)
        
        # Analyze preference distribution
        type_counts = df["preference_type"].value_counts().to_dict()
        weight_stats = {
            "mean": df["weight"].mean(),
            "median": df["weight"].median(),
            "std": df["weight"].std()
        }
        
        # Analyze most common preferences by type
        common_prefs = {}
        for pref_type in df["preference_type"].unique():
            type_data = df[df["preference_type"] == pref_type]
            value_counts = type_data["preference_value"].value_counts().head(5).to_dict()
            common_prefs[pref_type] = value_counts
        
        return {
            "preference_type_distribution": type_counts,
            "weight_statistics": weight_stats,
            "common_preferences": common_prefs
        }
    
    def _analyze_availability_patterns(self) -> Dict[str, Any]:
        """Analyze crew availability patterns."""
        availability = self.db.query(models.CrewAvailability).all()
        
        if not availability:
            return {"message": "No availability data available"}
        
        avail_data = []
        for a in availability:
            avail_data.append({
                "crew_id": a.crew_id,
                "availability_type": a.availability_type,
                "unavailable_from": a.unavailable_from,
                "unavailable_to": a.unavailable_to,
                "duration": (a.unavailable_to - a.unavailable_from).days
            })
        
        df = pd.DataFrame(avail_data)
        
        # Analyze availability type distribution
        type_counts = df["availability_type"].value_counts().to_dict()
        
        # Analyze duration statistics
        duration_stats = {
            "mean_days": df["duration"].mean(),
            "median_days": df["duration"].median(),
            "std_days": df["duration"].std()
        }
        
        # Analyze seasonal patterns
        df["month_from"] = pd.to_datetime(df["unavailable_from"]).dt.month
        seasonal_patterns = df["month_from"].value_counts().sort_index().to_dict()
        
        return {
            "availability_type_distribution": type_counts,
            "duration_statistics": duration_stats,
            "seasonal_patterns": seasonal_patterns
        }
    
    def _get_crew_availability_history(self, crew_id: int) -> pd.DataFrame:
        """Get historical availability data for a specific crew member."""
        availability = self.db.query(models.CrewAvailability).filter(
            models.CrewAvailability.crew_id == crew_id
        ).all()
        
        if not availability:
            return pd.DataFrame()
        
        data = []
        for a in availability:
            data.append({
                "crew_id": a.crew_id,
                "availability_type": a.availability_type,
                "unavailable_from": a.unavailable_from,
                "unavailable_to": a.unavailable_to,
                "day_of_week_from": a.unavailable_from.weekday(),
                "day_of_week_to": a.unavailable_to.weekday(),
                "duration": (a.unavailable_to - a.unavailable_from).days,
                "month_from": a.unavailable_from.month,
                "month_to": a.unavailable_to.month
            })
        
        return pd.DataFrame(data)
    
    def _simple_availability_prediction(self, crew_id: int, prediction_date: date) -> Dict[str, Any]:
        """Simple heuristic-based availability prediction."""
        # Check if crew has any unavailability records that overlap with the prediction date
        unavailable = self.db.query(models.CrewAvailability).filter(
            models.CrewAvailability.crew_id == crew_id,
            models.CrewAvailability.unavailable_from <= prediction_date,
            models.CrewAvailability.unavailable_to >= prediction_date,
            models.CrewAvailability.status == "approved"
        ).first()
        
        if unavailable:
            return {
                "crew_id": crew_id,
                "prediction_date": prediction_date.isoformat(),
                "available": False,
                "reason": unavailable.availability_type,
                "confidence": 0.9
            }
        else:
            return {
                "crew_id": crew_id,
                "prediction_date": prediction_date.isoformat(),
                "available": True,
                "confidence": 0.7
            }
    
    def _train_availability_model(self, availability_data: pd.DataFrame) -> RandomForestClassifier:
        """Train a model to predict crew availability."""
        # Prepare features
        features = ["day_of_week_from", "month_from", "duration"]
        X = availability_data[features].fillna(0)
        y = (availability_data["availability_type"] == "leave").astype(int)  # Simplified target
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        return model
    
    def _predict_availability(self, model: RandomForestClassifier, crew_id: int, prediction_date: date) -> Dict[str, Any]:
        """Make availability prediction using trained model."""
        # Prepare features for prediction
        day_of_week = prediction_date.weekday()
        month = prediction_date.month
        
        # Use average duration from historical data
        historical_data = self._get_crew_availability_history(crew_id)
        if not historical_data.empty:
            avg_duration = historical_data["duration"].mean()
        else:
            avg_duration = 7  # Default assumption
        
        # Make prediction
        features = np.array([[day_of_week, month, avg_duration]])
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0].max()
        
        return {
            "crew_id": crew_id,
            "prediction_date": prediction_date.isoformat(),
            "available": bool(1 - prediction),  # Inverted because 1 means leave in our model
            "confidence": float(probability)
        }
    
    def _get_performance_data(self) -> pd.DataFrame:
        """Get crew performance data."""
        # In a real implementation, we would have performance metrics in the database
        # For now, we'll simulate some performance data based on duty patterns
        duties = self.db.query(models.DutyPeriod).all()
        
        if not duties:
            return pd.DataFrame()
        
        # Group by crew and calculate performance metrics
        crew_performance = {}
        for duty in duties:
            crew_id = duty.crew_id
            if crew_id not in crew_performance:
                crew_performance[crew_id] = {
                    "total_duties": 0,
                    "total_hours": 0,
                    "on_time_duties": 0,
                    "late_duties": 0
                }
            
            crew_performance[crew_id]["total_duties"] += 1
            duration = (duty.duty_end_utc - duty.duty_start_utc).total_seconds() / 3600.0
            crew_performance[crew_id]["total_hours"] += duration
            
            # Simulate on-time performance (assuming 90% on-time as baseline)
            import random
            if random.random() < 0.9:
                crew_performance[crew_id]["on_time_duties"] += 1
            else:
                crew_performance[crew_id]["late_duties"] += 1
        
        # Convert to DataFrame
        data = []
        for crew_id, metrics in crew_performance.items():
            data.append({
                "crew_id": crew_id,
                "total_duties": metrics["total_duties"],
                "total_hours": metrics["total_hours"],
                "on_time_rate": metrics["on_time_duties"] / max(metrics["total_duties"], 1),
                "avg_hours_per_duty": metrics["total_hours"] / max(metrics["total_duties"], 1)
            })
        
        return pd.DataFrame(data)
    
    def _train_performance_model(self, performance_data: pd.DataFrame) -> RandomForestRegressor:
        """Train a model to predict crew performance."""
        if len(performance_data) < 5:
            raise ValueError("Insufficient data for training")
        
        # Prepare features and target
        features = ["total_duties", "total_hours", "avg_hours_per_duty"]
        X = performance_data[features].fillna(0)
        y = performance_data["on_time_rate"]  # Target variable
        
        # Train model
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        return model
    
    def _predict_crew_performance(self, model: RandomForestRegressor, crew_id: int, performance_data: pd.DataFrame) -> Optional[float]:
        """Predict performance for a specific crew member."""
        # Get crew's historical data
        crew_data = performance_data[performance_data["crew_id"] == crew_id]
        
        if crew_data.empty:
            return None
        
        # Prepare features for prediction
        features = ["total_duties", "total_hours", "avg_hours_per_duty"]
        X = crew_data[features].fillna(0)
        
        # Make prediction
        prediction = model.predict(X)[0]
        return float(prediction)
    
    def _get_performance_factors(self, crew_id: int, performance_data: pd.DataFrame) -> Dict[str, Any]:
        """Get factors that influence crew performance."""
        crew_data = performance_data[performance_data["crew_id"] == crew_id]
        
        if crew_data.empty:
            return {}
        
        return {
            "total_duties": int(crew_data["total_duties"].iloc[0]),
            "total_hours": float(crew_data["total_hours"].iloc[0]),
            "on_time_rate": float(crew_data["on_time_rate"].iloc[0]),
            "avg_hours_per_duty": float(crew_data["avg_hours_per_duty"].iloc[0])
        }
    
    def _get_active_crew(self) -> List[models.Crew]:
        """Get all active crew members."""
        return self.db.query(models.Crew).filter(models.Crew.status == "Active").all()
    
    def _get_disruption_history(self) -> pd.DataFrame:
        """Get historical disruption data."""
        disruptions = self.db.query(models.DisruptionRecord).all()
        
        if not disruptions:
            return pd.DataFrame()
        
        data = []
        for d in disruptions:
            data.append({
                "disruption_id": d.disruption_id,
                "flight_no": d.flight_no,
                "disruption_type": d.disruption_type,
                "disruption_date": d.disruption_date,
                "impact_duration": d.impact_duration or 0,
                "crew_id": d.crew_id,
                "day_of_week": d.disruption_date.weekday(),
                "month": d.disruption_date.month
            })
        
        return pd.DataFrame(data)
    
    def _analyze_disruption_patterns(self, disruption_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in disruption data."""
        # Analyze disruption type distribution
        type_counts = disruption_data["disruption_type"].value_counts().to_dict()
        
        # Analyze temporal patterns
        day_of_week_counts = disruption_data["day_of_week"].value_counts().sort_index().to_dict()
        month_counts = disruption_data["month"].value_counts().sort_index().to_dict()
        
        # Analyze impact severity
        impact_stats = {
            "mean_duration": disruption_data["impact_duration"].mean(),
            "median_duration": disruption_data["impact_duration"].median(),
            "max_duration": disruption_data["impact_duration"].max()
        }
        
        return {
            "disruption_type_distribution": type_counts,
            "day_of_week_patterns": day_of_week_counts,
            "monthly_patterns": month_counts,
            "impact_statistics": impact_stats
        }
    
    def _identify_burnout_risks(self) -> List[Dict[str, Any]]:
        """Identify crew members at risk of burnout based on duty patterns."""
        # Get recent duty data (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_duties = self.db.query(models.DutyPeriod).filter(
            models.DutyPeriod.duty_start_utc >= thirty_days_ago
        ).all()
        
        if not recent_duties:
            return []
        
        # Count duties per crew member
        duty_counts = {}
        for duty in recent_duties:
            crew_id = duty.crew_id
            if crew_id not in duty_counts:
                duty_counts[crew_id] = 0
            duty_counts[crew_id] += 1
        
        # Identify crew with excessive duties (more than 20 in 30 days)
        high_duty_crew = []
        for crew_id, count in duty_counts.items():
            if count > 20:
                crew = self.db.query(models.Crew).filter(models.Crew.crew_id == crew_id).first()
                if crew:
                    high_duty_crew.append({
                        "crew_id": crew_id,
                        "crew_name": crew.name,
                        "duty_count_last_30_days": count,
                        "risk_level": "high"
                    })
        
        return high_duty_crew
    
    def _identify_scheduling_conflicts(self) -> List[Dict[str, Any]]:
        """Identify potential scheduling conflicts."""
        # This is a simplified implementation
        # In a real system, we would check for overlapping duties, insufficient rest, etc.
        return []

def analyze_crew_patterns(db: Session) -> Dict[str, Any]:
    """
    Analyze crew patterns using predictive analytics.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary containing pattern analysis results
    """
    predictor = CrewRosteringPredictor(db)
    return predictor.analyze_crew_patterns()

def predict_crew_availability(db: Session, crew_id: int, prediction_date: date) -> Dict[str, Any]:
    """
    Predict crew availability for a specific date.
    
    Args:
        db: Database session
        crew_id: ID of the crew member
        prediction_date: Date for which to predict availability
        
    Returns:
        Dictionary containing availability prediction
    """
    predictor = CrewRosteringPredictor(db)
    return predictor.predict_crew_availability(crew_id, prediction_date)

def predict_crew_performance(db: Session) -> Dict[str, Any]:
    """
    Predict crew performance based on historical data.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary containing performance predictions
    """
    predictor = CrewRosteringPredictor(db)
    return predictor.predict_crew_performance()

def identify_risk_patterns(db: Session) -> Dict[str, Any]:
    """
    Identify risk patterns in crew scheduling that could lead to disruptions.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary containing identified risks
    """
    predictor = CrewRosteringPredictor(db)
    return predictor.identify_risk_patterns()