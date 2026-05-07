"""
MongoDB database connection and management
"""
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, ConnectionFailure
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


class MongoDB:
    """MongoDB connection manager (Singleton pattern)"""
    
    _instance = None
    _client: Optional[MongoClient] = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self.connect()
    
    def connect(self):
        """Connect to MongoDB Atlas"""
        mongo_uri = os.getenv("MONGODB_URI")
        db_name = os.getenv("MONGODB_DB_NAME", "lmaro_db")
        
        if not mongo_uri:
            raise ValueError("MONGODB_URI not set in environment variables")
        
        try:
            self._client = MongoClient(mongo_uri)
            # Test connection
            self._client.admin.command('ping')
            self._db = self._client[db_name]
            print(f"✓ Connected to MongoDB: {db_name}")
            
            # Create indexes
            self._setup_indexes()
            
        except ConnectionFailure as e:
            print(f"✗ MongoDB connection failed: {e}")
            raise
    
    def _setup_indexes(self):
        """Create database indexes for performance"""
        try:
            # Users collection - unique username and email
            self._db.users.create_index("username", unique=True)
            self._db.users.create_index("email", unique=True)
            
            # Resumes collection - compound index
            self._db.resumes.create_index([("username", 1), ("job_id", 1)])
            
            # Jobs collection
            self._db.jobs.create_index("job_id", unique=True)
            
            print("✓ Database indexes created")
        except Exception as e:
            print(f"⚠ Index creation warning: {e}")
    
    @property
    def db(self):
        """Get database instance"""
        if self._db is None:
            self.connect()
        return self._db
    
    @property
    def users(self):
        """Get users collection"""
        return self.db.users
    
    @property
    def resumes(self):
        """Get resumes collection"""
        return self.db.resumes
    
    @property
    def jobs(self):
        """Get jobs collection"""
        return self.db.jobs
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            print("✓ MongoDB connection closed")


# Global database instance
mongodb = MongoDB()
