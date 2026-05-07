"""
Test Profile Builder Agent

Quick test to verify the ReAct agent is working properly.
"""
import sys
import os

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_profile_builder():
    """Test the Profile Builder Agent"""
    
    print("\n" + "="*60)
    print("🧪 PROFILE BUILDER AGENT TEST")
    print("="*60)
    
    # Import agent
    from src.profile.builder import ProfileBuilderAgent, ProfileBuilderInput
    
    # Create agent (no DB connections for test)
    print("\n📦 Creating agent...")
    agent = ProfileBuilderAgent(verbose=True)
    print("✅ Agent created!")
    
    # Test input - work experience
    test_text = """
    I worked at LSEG (London Stock Exchange Group) from August 2022 to December 2024 
    as a Senior Software Engineer. My key achievements:
    - Built an event-driven data pipeline using AWS Lambda that processed 7.5 million records
    - Reduced system latency by 40% through optimization
    - Led a team of 5 engineers
    - Technologies: Python, AWS Lambda, S3, DynamoDB, SQS, Kafka
    
    Before that, I was at Infosys from October 2020 to August 2022 as a Systems Engineer.
    I developed RPA bots using Automation Anywhere and Python.
    """
    
    print("\n" + "="*60)
    print("📝 Test Input:")
    print("="*60)
    print(test_text.strip())
    
    # Process input
    print("\n" + "="*60)
    print("🤖 Agent Processing...")
    print("="*60)
    
    response = agent.process_input(ProfileBuilderInput(
        user_id="test_user_123",
        message=test_text
    ))
    
    # Show response
    print("\n" + "="*60)
    print("📤 Agent Response:")
    print("="*60)
    print(f"Session ID: {response.session_id}")
    print(f"Action: {response.action}")
    print(f"Waiting for user: {response.waiting_for_user}")
    print(f"Pending entities: {response.pending_count}")
    print(f"Confirmed entities: {response.confirmed_count}")
    print(f"\n💬 Message:\n{response.message}")
    
    if response.entity_for_confirmation:
        print(f"\n📋 Entity for Confirmation:")
        print(f"  Type: {response.entity_for_confirmation.entity_type}")
        print(f"  Data: {response.entity_for_confirmation.data}")
    
    # Test follow-up
    if response.waiting_for_user:
        print("\n" + "="*60)
        print("🔄 Simulating User Confirmation...")
        print("="*60)
        
        # Simulate user saying "yes, that's correct"
        response2 = agent.process_input(ProfileBuilderInput(
            user_id="test_user_123",
            session_id=response.session_id,
            message="Yes, that looks correct. Please save it."
        ))
        
        print(f"\n💬 Follow-up Response:\n{response2.message}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)
    
    return response


def test_api_endpoint():
    """Test the API endpoint (requires server running)"""
    import requests
    
    print("\n" + "="*60)
    print("🌐 API ENDPOINT TEST")
    print("="*60)
    
    url = "http://localhost:8000/api/profile/builder/test"
    
    test_message = "I have 5 years of Python experience and built a machine learning pipeline at Google."
    
    try:
        response = requests.post(
            url,
            params={"message": test_message}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response:")
            print(f"  Session: {data.get('session_id')}")
            print(f"  Action: {data.get('action')}")
            print(f"  Message: {data.get('message', '')[:200]}...")
        else:
            print(f"❌ API Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running. Start with: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Profile Builder")
    parser.add_argument("--api", action="store_true", help="Test API endpoint")
    args = parser.parse_args()
    
    if args.api:
        test_api_endpoint()
    else:
        test_profile_builder()
