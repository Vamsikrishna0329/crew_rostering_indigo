
# Crew Rostering — Full Stack (SQLite + LLM, LARGE DB)

Includes:
- Backend (FastAPI + SQLAlchemy + **large SQLite** DB)
- LLM endpoints (OpenAI-compatible; defaults to Groq)
- Frontend (React + Vite + Tailwind)
- Preseeded SQLite DB: **~1,000 crew**, **~13,500 flights** (90 days × 150/day)
- **Google OR-Tools optimization** for complex scheduling and resource allocation
- **Scikit-learn predictive analytics** for pattern analysis and data-driven decision making

## Run (Windows, no Docker)
### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000

# If you encounter dependency conflicts, try:
# pip install --upgrade pip
# pip install -r requirements.txt --use-deprecated=legacy-resolver
```
API: http://127.0.0.1:8000/docs

### Frontend
```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```
UI: http://localhost:5173

## New Features

### Optimization Methods
- **Simple Heuristics**: Original optimization algorithm using rule-based heuristics
- **OR-Tools**: Advanced constraint satisfaction optimization using Google OR-Tools

### Predictive Analytics
- **Crew Pattern Analysis**: Clustering analysis to identify crew duty patterns
- **Availability Prediction**: Machine learning models to predict crew availability
- **Performance Prediction**: Predictive models for crew performance
- **Risk Pattern Identification**: Analysis of scheduling risks and potential disruptions

### API Endpoints
- `/v1/rosters/generate` - Generate roster with selectable optimization method
- `/v1/analytics/patterns/crew` - Analyze crew patterns
- `/v1/analytics/predict/availability/{crew_id}/{prediction_date}` - Predict crew availability
- `/v1/analytics/predict/performance` - Predict crew performance
- `/v1/analytics/risks` - Identify risk patterns
