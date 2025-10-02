"""
Authentication Test Suite
Tests API key authentication for all protected endpoints
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "test_key")  # Use actual key from .env or test key

print("=" * 60)
print("API Authentication Test Suite")
print("=" * 60)
print(f"Base URL: {BASE_URL}")
print(f"API Key: {API_KEY[:10]}..." if len(API_KEY) > 10 else f"API Key: {API_KEY}")
print("=" * 60)

def test_health_endpoint():
    """Test public health endpoint (no auth required)"""
    print("\n[TEST 1] Health Endpoint (Public)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASSED: Health endpoint accessible without authentication")
            return True
        else:
            print("❌ FAILED: Health endpoint returned unexpected status")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_root_endpoint():
    """Test public root endpoint (no auth required)"""
    print("\n[TEST 2] Root Endpoint (Public)")
    print("-" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ PASSED: Root endpoint accessible without authentication")
            return True
        else:
            print("❌ FAILED: Root endpoint returned unexpected status")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_chat_without_auth():
    """Test chat endpoint without authentication (should fail)"""
    print("\n[TEST 3] POST /api/chat Without Authentication")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": "Hello", "session_id": "test"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 401:
            print("✅ PASSED: Chat endpoint correctly rejects unauthenticated requests")
            return True
        else:
            print("❌ FAILED: Chat endpoint should return 401 without auth")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_chat_with_invalid_auth():
    """Test chat endpoint with invalid API key (should fail)"""
    print("\n[TEST 4] POST /api/chat With Invalid API Key")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"X-API-Key": "invalid_key_12345"},
            json={"message": "Hello", "session_id": "test"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 403:
            print("✅ PASSED: Chat endpoint correctly rejects invalid API key")
            return True
        else:
            print("❌ FAILED: Chat endpoint should return 403 for invalid key")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_chat_with_valid_auth():
    """Test chat endpoint with valid API key (should succeed)"""
    print("\n[TEST 5] POST /api/chat With Valid API Key")
    print("-" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            headers={"X-API-Key": API_KEY},
            json={"message": "Hello, this is a test", "session_id": "test"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("✅ PASSED: Chat endpoint accessible with valid API key")
            return True
        else:
            print(f"Response: {response.text}")
            print("❌ FAILED: Chat endpoint should return 200 with valid key")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_stream_without_auth():
    """Test stream endpoint without authentication (should fail)"""
    print("\n[TEST 6] GET /api/chat/stream Without Authentication")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/chat/stream",
            params={"message": "Hello"}
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print("✅ PASSED: Stream endpoint correctly rejects unauthenticated requests")
            return True
        else:
            print(f"Response: {response.text[:200]}")
            print("❌ FAILED: Stream endpoint should return 401 without auth")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_stream_with_valid_auth():
    """Test stream endpoint with valid API key (should succeed)"""
    print("\n[TEST 7] GET /api/chat/stream With Valid API Key")
    print("-" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/chat/stream",
            headers={"X-API-Key": API_KEY},
            params={"message": "Hello"},
            stream=True
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # Read first few bytes to verify streaming works
            print("Stream started successfully")
            print("✅ PASSED: Stream endpoint accessible with valid API key")
            response.close()
            return True
        else:
            print(f"Response: {response.text[:200]}")
            print("❌ FAILED: Stream endpoint should return 200 with valid key")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def run_all_tests():
    """Run all authentication tests"""
    print("\n" + "=" * 60)
    print("Starting Authentication Tests...")
    print("=" * 60)
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Root Endpoint", test_root_endpoint),
        ("Chat Without Auth", test_chat_without_auth),
        ("Chat With Invalid Key", test_chat_with_invalid_auth),
        ("Chat With Valid Key", test_chat_with_valid_auth),
        ("Stream Without Auth", test_stream_without_auth),
        ("Stream With Valid Key", test_stream_with_valid_auth),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {str(e)}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    print("=" * 60)
    
    return passed == total

if __name__ == "__main__":
    try:
        # Check if server is running
        print("\nChecking if server is running...")
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print("✅ Server is running\n")
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Server is not running!")
        print("Please start the server first: python main.py")
        exit(1)
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        exit(1)
    
    # Run tests
    success = run_all_tests()
    exit(0 if success else 1)