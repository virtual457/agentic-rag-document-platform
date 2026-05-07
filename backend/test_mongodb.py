"""
Quick test to verify MongoDB connection
"""
from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Get connection string
mongo_uri = os.getenv("MONGODB_URI")

if not mongo_uri:
    print("❌ MONGODB_URI not found in .env file")
    exit(1)

print("Testing MongoDB connection...")
print(f"URI: {mongo_uri[:50]}...")  # Show first 50 chars

try:
    # Try to connect
    client = MongoClient(mongo_uri)
    
    # Test connection
    client.admin.command('ping')
    
    print("✅ SUCCESS! MongoDB connection works!")
    print(f"Connected to: lmaro_db")
    
    # List databases
    db_list = client.list_database_names()
    print(f"\nAvailable databases: {db_list}")
    
    client.close()
    
except Exception as e:
    print(f"❌ FAILED! Connection error:")
    print(f"Error: {e}")
    print("\n🔧 To fix:")
    print("1. Check password in MongoDB Atlas")
    print("2. Make sure IP is whitelisted (0.0.0.0/0)")
    print("3. Verify username is correct: chandankeelara_db_user")
