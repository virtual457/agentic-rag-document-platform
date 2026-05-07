"""
Test authentication system with user ID-based ChromaDB
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_register():
    """Test user registration"""
    print("\n=== Testing User Registration ===")
    
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "password123",
        "full_name": "Test User Two"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ User registered successfully!")
        print(f"User ID: {data['user']['user_id']}")
        print(f"Username: {data['user']['username']}")
        print(f"Email: {data['user']['email']}")
        print(f"Token: {data['access_token'][:50]}...")
        print(f"\n✓ ChromaDB folder created: chromadb_store/user_{data['user']['user_id']}/")
        return data['access_token'], data['user']['user_id']
    else:
        print(f"✗ Registration failed: {response.json()}")
        return None, None

def test_login(username="testuser2", password="password123"):
    """Test user login"""
    print("\n=== Testing User Login ===")
    
    credentials = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=credentials)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Login successful!")
        print(f"User ID: {data['user']['user_id']}")
        print(f"Username: {data['user']['username']}")
        print(f"Token: {data['access_token'][:50]}...")
        return data['access_token'], data['user']['user_id']
    else:
        print(f"✗ Login failed: {response.json()}")
        return None, None

def test_get_current_user(token):
    """Test getting current user info"""
    print("\n=== Testing Get Current User ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ User info retrieved!")
        print(f"Response: {json.dumps(data, indent=2, default=str)}")
        return True
    else:
        print(f"✗ Failed: {response.json()}")
        return False

def test_protected_route_without_token():
    """Test accessing protected route without token"""
    print("\n=== Testing Protected Route Without Token ===")
    
    response = requests.get(f"{BASE_URL}/api/auth/me")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✓ Correctly denied access without token")
        return True
    else:
        print(f"✗ Should have returned 401")
        return False

def test_chromadb_folder_exists(user_id):
    """Test if ChromaDB folder was created"""
    print("\n=== Testing ChromaDB Folder Creation ===")
    import os
    
    folder_path = f"chromadb_store/user_{user_id}"
    
    if os.path.exists(folder_path):
        print(f"✓ ChromaDB folder exists: {folder_path}")
        return True
    else:
        print(f"✗ ChromaDB folder NOT found: {folder_path}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("LMARO Authentication System Tests (ID-Based)")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n✗ Health check failed - is the server running?")
        return
    
    # Test 2: Register new user
    token, user_id = test_register()
    if not token:
        print("\n⚠ Registration failed (user might already exist)")
        # Try logging in with existing user
        token, user_id = test_login()
        if not token:
            print("\n✗ Both registration and login failed!")
            return
    
    # Test 3: Verify ChromaDB folder was created
    test_chromadb_folder_exists(user_id)
    
    # Test 4: Get current user info
    test_get_current_user(token)
    
    # Test 5: Protected route without token
    test_protected_route_without_token()
    
    # Test 6: Login again
    test_login()
    
    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print(f"✓ User-specific ChromaDB: chromadb_store/user_{user_id}/")
    print("=" * 60)

if __name__ == "__main__":
    main()
