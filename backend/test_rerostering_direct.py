import requests
import json

# Test the rerostering functionality directly
BASE_URL = "http://127.0.0.1:8000/v1"

def test_direct_request():
    """Test sending a direct request to see what happens"""
    print("Testing direct request...")
    
    # Test with exact string matching
    payload = {
        "flight_no": "6E1002",
        "type": "Cancellation"
    }
    
    print(f"Sending payload: {payload}")
    print(f"Type field: '{payload['type']}'")
    print(f"Type field length: {len(payload['type'])}")
    print(f"Type field bytes: {payload['type'].encode()}")
    
    try:
        response = requests.post(f"{BASE_URL}/reroster", json=payload)
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_direct_request()