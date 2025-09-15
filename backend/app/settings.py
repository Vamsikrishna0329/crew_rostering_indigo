
from pydantic import BaseModel
import os
class Settings(BaseModel):
    app_env: str = os.getenv("APP_ENV", "dev")
    sqlite_path: str = os.getenv("SQLITE_PATH", "./data/crew_rostering.db")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    llm_model: str = os.getenv("LLM_MODEL", "llama-3.1-70b-versatile")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
settings = Settings()
