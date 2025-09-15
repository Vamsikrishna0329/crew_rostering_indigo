
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables from .env file in the backend directory
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(env_path)

from app.api.v1 import roster, rerostering, health, ai, analytics
app = FastAPI(title="Crew Rostering (SQLite + LLM, Large)", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/v1/health", tags=["health"])
app.include_router(roster.router, prefix="/v1/rosters", tags=["rosters"])
app.include_router(rerostering.router, prefix="/v1/reroster", tags=["reroster"])
app.include_router(ai.router, prefix="/v1/ai", tags=["ai"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["analytics"])
