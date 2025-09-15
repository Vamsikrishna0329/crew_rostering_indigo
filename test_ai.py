import requests

# Test AI suggest patch functionality
try:
    payload = {
        "flight_no": "6E1000"
    }
    
    print("Testing AI suggest patch...")
    print(f"Payload: {payload}")
    
    response = requests.post("http://127.0.0.1:8000/v1/ai/reroster_suggest", json=payload, timeout=30)
    print("AI suggest patch response:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Success! AI suggest patch response:")
        print(data)
    else:
        print("Error:", response.text)
except requests.exceptions.RequestException as e:
    print("AI suggest patch failed:", e)
except Exception as e:
    print("Unexpected error:", e)

print("\n" + "="*50 + "\n")

# Test AI ask functionality
try:
    payload = {
        "question": "How many crew members are in the database?"
    }
    
    print("Testing AI ask...")
    print(f"Payload: {payload}")
    
    response = requests.post("http://127.0.0.1:8000/v1/ai/ask", json=payload, timeout=30)
    print("AI ask response:", response.status_code)
    if response.status_code == 200:
        data = response.json()
        print("Success! AI ask response:")
        print(data)
    else:
        print("Error:", response.text)
except requests.exceptions.RequestException as e:
    print("AI ask failed:", e)
except Exception as e:
    print("Unexpected error:", e)