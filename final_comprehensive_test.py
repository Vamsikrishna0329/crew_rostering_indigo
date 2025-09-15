#!/usr/bin/env python3
"""
Final comprehensive test script for the Crew Rostering application.
This script verifies all functionality is working correctly after fixes.
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

def test_frontend_access():
    """Test that frontend is accessible"""
    print("Testing frontend accessibility...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("[PASS] Frontend is accessible")
            return True
        else:
            print(f"[FAIL] Frontend returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Frontend not accessible: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    print("Testing backend health...")
    try:
        response = requests.get(f"{BACKEND_URL}/v1/health", timeout=5)
        if response.status_code == 200:
            print("[PASS] Backend health check passed")
            return True
        else:
            print(f"[FAIL] Backend health check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] Backend health check failed: {e}")
        return False

def test_roster_generation(method="simple-heuristics"):
    """Test roster generation with specified method"""
    print(f"Testing roster generation with {method}...")
    try:
        payload = {
            "period_start": "2025-09-08",
            "period_end": "2025-09-14",
            "optimization_method": method
        }
        response = requests.post(
            f"{BACKEND_URL}/v1/rosters/generate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] Roster generation with {method} successful")
            print(f"  - Status: {data['status']}")
            print(f"  - Period: {data['period_start']} to {data['period_end']}")
            print(f"  - Assignments: {len(data['assignments'])}")
            print(f"  - Flights assigned: {data['kpis']['flights_assigned']}")
            return True
        else:
            print(f"[FAIL] Roster generation with {method} failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Roster generation with {method} failed: {e}")
        return False

def test_rerostering_cancellation():
    """Test cancellation re-rostering"""
    print("Testing cancellation re-rostering...")
    try:
        payload = {
            "flight_no": "6E1003",
            "type": "Cancellation"
        }
        response = requests.post(
            f"{BACKEND_URL}/v1/reroster",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print("[PASS] Cancellation re-rostering successful")
            print(f"  - Status: {data['status']}")
            print(f"  - Message: {data['patch']['message']}")
            print(f"  - Reassignments found: {len(data['patch']['reassignments'])}")
            return True
        else:
            print(f"[FAIL] Cancellation re-rostering failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Cancellation re-rostering failed: {e}")
        return False

def test_rerostering_delay():
    """Test delay re-rostering"""
    print("Testing delay re-rostering...")
    try:
        payload = {
            "flight_no": "6E1003",
            "type": "Delay",
            "delay_minutes": 120
        }
        response = requests.post(
            f"{BACKEND_URL}/v1/reroster",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print("[PASS] Delay re-rostering successful")
            print(f"  - Status: {data['status']}")
            print(f"  - Flight: {data['patch']['flight_no']}")
            print(f"  - Feasible: {data['patch']['feasible']}")
            return True
        else:
            print(f"[FAIL] Delay re-rostering failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Delay re-rostering failed: {e}")
        return False

def test_rerostering_crew_unavailability():
    """Test crew unavailability re-rostering"""
    print("Testing crew unavailability re-rostering...")
    try:
        payload = {
            "flight_no": "6E1003",
            "type": "CrewUnavailability",
            "crew_id": 1,
            "unavailable_from": "2025-09-08",
            "unavailable_to": "2025-09-10"
        }
        response = requests.post(
            f"{BACKEND_URL}/v1/reroster",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print("[PASS] Crew unavailability re-rostering successful")
            print(f"  - Status: {data['status']}")
            print(f"  - Crew: {data['patch']['crew_name']}")
            print(f"  - Message: {data['patch']['message']}")
            print(f"  - Reassignments found: {len(data['patch']['reassignments'])}")
            return True
        else:
            print(f"[FAIL] Crew unavailability re-rostering failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"[FAIL] Crew unavailability re-rostering failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("CREW ROSTERING APPLICATION - COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Test components
    tests = [
        test_frontend_access,
        test_backend_health,
        lambda: test_roster_generation("simple-heuristics"),
        lambda: test_roster_generation("or-tools"),
        test_rerostering_cancellation,
        test_rerostering_delay,
        test_rerostering_crew_unavailability
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"[FAIL] Test failed with exception: {e}")
            results.append(False)
            print()
        # Small delay between tests
        time.sleep(1)
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("ALL TESTS PASSED! The application is working correctly.")
        return 0
    else:
        print("Some tests failed. Please check the application.")
        return 1

if __name__ == "__main__":
    exit(main())