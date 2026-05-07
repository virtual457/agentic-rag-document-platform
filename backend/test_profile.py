"""
Test profile completion system
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def register_and_login():
    """Register new user and get token"""
    print("\n=== Registering Test User ===")
    
    user_data = {
        "username": "profiletest",
        "email": "profiletest@example.com",
        "password": "password123",
        "full_name": "Profile Test User"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    
    if response.status_code == 201:
        data = response.json()
        print(f"✓ User registered: {data['user']['username']}")
        print(f"✓ Initial completion: {data['user']['profile_completion']['percentage']}%")
        return data['access_token']
    else:
        # Try login if user exists
        print("User exists, logging in...")
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        if response.status_code == 200:
            return response.json()['access_token']
        return None

def get_profile(token):
    """Get current profile"""
    print("\n=== Getting Profile ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/profile/me", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        completion = data['profile_completion']
        print(f"Completion: {completion['percentage']}%")
        print(f"Status: {completion['status']}")
        print(f"Feedback: {completion['feedback']}")
        return data
    else:
        print(f"✗ Failed: {response.json()}")
        return None

def update_profile_partial(token):
    """Add some work experience"""
    print("\n=== Adding Work Experience ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    profile_update = {
        "profile_data": {
            "work_experience": [
                {
                    "company": "Google",
                    "role": "Software Engineer",
                    "duration": "2020-2022",
                    "achievements": [
                        "Built scalable microservices",
                        "Reduced latency by 40%"
                    ]
                }
            ]
        },
        "analyze": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/profile/update",
        json=profile_update,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        completion = data['completion']
        print(f"✓ Profile updated!")
        print(f"New Completion: {completion['percentage']}%")
        print(f"Status: {completion['status']}")
        print(f"Feedback: {completion['feedback']}")
        print(f"Missing: {completion['missing_sections']}")
        return data
    else:
        print(f"✗ Failed: {response.json()}")
        return None

def update_profile_full(token):
    """Add complete profile data"""
    print("\n=== Adding Complete Profile ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    profile_update = {
        "profile_data": {
            "education": [
                {
                    "degree": "B.E. Computer Science",
                    "institution": "NMIT Bangalore",
                    "year": "2020",
                    "gpa": "8.76/10"
                }
            ],
            "work_experience": [
                {
                    "company": "LSEG",
                    "role": "Senior Software Engineer",
                    "duration": "Aug 2022 - Dec 2024",
                    "achievements": [
                        "Built event-driven pipeline for 7.5M records",
                        "Reduced latency by 40%",
                        "Mentored 5 engineers"
                    ]
                }
            ],
            "skills": [
                "Python", "Java", "AWS", "Kubernetes", "Docker",
                "Spring Boot", "FastAPI", "MongoDB", "PostgreSQL"
            ],
            "projects": [
                {
                    "name": "LMARO",
                    "description": "AI resume optimizer with multi-agent system",
                    "technologies": ["Python", "FastAPI", "LangChain", "ChromaDB"],
                    "highlights": [
                        "RAG implementation",
                        "Multi-agent coordination"
                    ]
                }
            ],
            "certifications": [
                "AWS Certified Cloud Practitioner"
            ]
        },
        "analyze": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/profile/update",
        json=profile_update,
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        completion = data['completion']
        print(f"✓ Full profile updated!")
        print(f"Final Completion: {completion['percentage']}%")
        print(f"Status: {completion['status']}")
        print(f"Feedback: {completion['feedback'][:200]}...")
        if completion.get('strengths'):
            print(f"Strengths: {completion['strengths']}")
        if completion.get('next_steps'):
            print(f"Next Steps: {completion['next_steps']}")
        return data
    else:
        print(f"✗ Failed: {response.json()}")
        return None

def analyze_profile(token):
    """Manually trigger profile analysis"""
    print("\n=== Analyzing Current Profile ===")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/api/profile/analyze", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Analysis complete!")
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"✗ Failed: {response.json()}")
        return None

def main():
    """Run all profile tests"""
    print("=" * 60)
    print("LMARO Profile Completion System Tests")
    print("=" * 60)
    
    # Step 1: Register/Login
    token = register_and_login()
    if not token:
        print("✗ Authentication failed")
        return
    
    # Step 2: Get initial profile (should be 0%)
    get_profile(token)
    
    # Step 3: Add partial data
    update_profile_partial(token)
    
    # Step 4: Add complete profile
    update_profile_full(token)
    
    # Step 5: Manually analyze
    analyze_profile(token)
    
    print("\n" + "=" * 60)
    print("✓ All profile tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
