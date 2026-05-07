"""
User authentication manager using MongoDB
"""
from datetime import datetime
from typing import Optional
from pymongo.errors import DuplicateKeyError
import os

from .models import UserRegister, UserInDB, UserResponse, UserProfile, ProfileCompletionStatus
from .security import get_password_hash, verify_password
from .database import mongodb


class UserAuthManager:
    """Manages user authentication with MongoDB"""
    
    def __init__(self):
        self.db = mongodb
        self.chromadb_base_path = os.getenv("CHROMADB_PATH", "./chromadb_store")
    
    def user_exists(self, username: str) -> bool:
        """Check if username exists"""
        return self.db.users.find_one({"username": username}) is not None
    
    def email_exists(self, email: str) -> bool:
        """Check if email exists"""
        return self.db.users.find_one({"email": email}) is not None
    
    def create_user(self, user_data: UserRegister) -> UserInDB:
        """
        Create new user in MongoDB with initialized profile
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user object
            
        Raises:
            ValueError: If user already exists
        """
        # Check if user exists
        if self.user_exists(user_data.username):
            raise ValueError(f"Username '{user_data.username}' already exists")
        
        if self.email_exists(user_data.email):
            raise ValueError(f"Email '{user_data.email}' already registered")
        
        # Create user document with initialized profile
        user_doc = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": get_password_hash(user_data.password),
            "created_at": datetime.utcnow(),
            "is_active": True,
            # Initialize empty profile
            "profile": {
                "personal": {
                    "name": user_data.full_name,
                    "email": user_data.email
                },
                "education": [],
                "work_experience": [],
                "skills": [],
                "projects": [],
                "certifications": [],
                "achievements": []
            },
            # Initialize completion status at 0%
            "profile_completion": {
                "percentage": 0,
                "status": "incomplete",
                "feedback": "Profile just created. Please add your work experience, education, skills, and projects to unlock resume generation.",
                "missing_sections": ["education", "work_experience", "skills", "projects"],
                "last_analyzed": datetime.utcnow()
            }
        }
        
        try:
            # Insert into MongoDB
            result = self.db.users.insert_one(user_doc)
            user_id = str(result.inserted_id)  # Get MongoDB ObjectId
            
            # Create user's ChromaDB directory using user_id
            user_chromadb_path = os.path.join(self.chromadb_base_path, f"user_{user_id}")
            os.makedirs(user_chromadb_path, exist_ok=True)
            
            # Return user object with ID
            user_in_db = UserInDB(
                user_id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=user_doc["hashed_password"],
                created_at=user_doc["created_at"],
                is_active=user_doc["is_active"],
                profile=UserProfile(**user_doc["profile"]),
                profile_completion=ProfileCompletionStatus(**user_doc["profile_completion"])
            )
            
            print(f"✓ User created: {user_data.username} (ID: {user_id})")
            print(f"✓ Profile initialized at 0% completion")
            print(f"✓ ChromaDB folder created: {user_chromadb_path}")
            
            return user_in_db
            
        except DuplicateKeyError:
            raise ValueError("User already exists (duplicate key)")
    
    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """
        Get user by user_id (MongoDB ObjectId)
        
        Args:
            user_id: MongoDB ObjectId as string
            
        Returns:
            User object if found, None otherwise
        """
        from bson import ObjectId
        
        try:
            user_doc = self.db.users.find_one({"_id": ObjectId(user_id)})
        except:
            return None
        
        if not user_doc:
            return None
        
        # Handle profile and profile_completion with defaults
        profile_data = user_doc.get('profile', {
            "personal": {},
            "education": [],
            "work_experience": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "achievements": []
        })
        
        completion_data = user_doc.get('profile_completion', {
            "percentage": 0,
            "status": "incomplete",
            "feedback": "Profile needs to be filled",
            "missing_sections": [],
            "last_analyzed": None
        })
        
        return UserInDB(
            user_id=str(user_doc['_id']),
            username=user_doc['username'],
            email=user_doc['email'],
            full_name=user_doc['full_name'],
            hashed_password=user_doc['hashed_password'],
            created_at=user_doc['created_at'],
            is_active=user_doc['is_active'],
            profile=UserProfile(**profile_data),
            profile_completion=ProfileCompletionStatus(**completion_data)
        )
    
    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """
        Get user by username
        
        Args:
            username: Username to lookup
            
        Returns:
            User object if found, None otherwise
        """
        user_doc = self.db.users.find_one({"username": username})
        
        if not user_doc:
            return None
        
        # Handle profile and profile_completion with defaults
        profile_data = user_doc.get('profile', {
            "personal": {},
            "education": [],
            "work_experience": [],
            "skills": [],
            "projects": [],
            "certifications": [],
            "achievements": []
        })
        
        completion_data = user_doc.get('profile_completion', {
            "percentage": 0,
            "status": "incomplete",
            "feedback": "Profile needs to be filled",
            "missing_sections": [],
            "last_analyzed": None
        })
        
        return UserInDB(
            user_id=str(user_doc['_id']),
            username=user_doc['username'],
            email=user_doc['email'],
            full_name=user_doc['full_name'],
            hashed_password=user_doc['hashed_password'],
            created_at=user_doc['created_at'],
            is_active=user_doc['is_active'],
            profile=UserProfile(**profile_data),
            profile_completion=ProfileCompletionStatus(**completion_data)
        )
    
    def get_user_response(self, user_id: str) -> Optional[UserResponse]:
        """Get user data without password (for API responses)"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at,
            is_active=user.is_active,
            profile_completion=user.profile_completion
        )
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """
        Authenticate user with username/password
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User object if authenticated, None otherwise
        """
        user = self.get_user_by_username(username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    def update_user(self, user_id: str, updates: dict) -> bool:
        """
        Update user fields
        
        Args:
            user_id: MongoDB ObjectId as string
            updates: Dictionary of fields to update
            
        Returns:
            True if updated, False if user not found
        """
        from bson import ObjectId
        
        try:
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            return result.modified_count > 0
        except:
            return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        return self.update_user(user_id, {"is_active": False})


# Global instance
user_auth_manager = UserAuthManager()
