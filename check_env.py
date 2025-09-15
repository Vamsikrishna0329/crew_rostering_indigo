import os
from dotenv import load_dotenv

# Load environment variables from .env file in the backend directory
env_path = os.path.join("backend", ".env")
load_dotenv(env_path)

print("Environment variables:")
print(f"LLM_API_KEY: {os.getenv('LLM_API_KEY')}")
print(f"LLM_BASE_URL: {os.getenv('LLM_BASE_URL')}")
print(f"LLM_MODEL: {os.getenv('LLM_MODEL')}")

# Check if settings module can load them
try:
    from backend.app.settings import settings
    print("\nSettings module:")
    print(f"llm_api_key: {settings.llm_api_key}")
    print(f"llm_base_url: {settings.llm_base_url}")
    print(f"llm_model: {settings.llm_model}")
except Exception as e:
    print(f"\nError loading settings: {e}")