import requests
import time

# Test if the backend is running
try:
    response = requests.get("http://127.0.0.1:8000/v1/health", timeout=5)
    print("Backend is running:", response.status_code)
    print("Health check response:", response.json())
except requests.exceptions.RequestException as e:
    print("Backend is not running or not accessible:", e)

# Test database connectivity through the health endpoint
try:
    response = requests.get("http://127.0.0.1:8000/v1/health/db", timeout=5)
    print("Database health check:", response.status_code)
    print("Database health response:", response.json())
except requests.exceptions.RequestException as e:
    print("Database health check failed:", e)