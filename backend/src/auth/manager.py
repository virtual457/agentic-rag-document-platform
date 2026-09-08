"""User authentication manager (MongoDB-backed)."""
from datetime import datetime
from typing import Optional

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from .database import mongodb
from .models import UserInDB, UserRegister, UserResponse
from .security import get_password_hash, verify_password


def _doc_to_user(doc: dict) -> UserInDB:
    return UserInDB(
        user_id=str(doc["_id"]),
        username=doc["username"],
        email=doc["email"],
        full_name=doc.get("full_name") or doc["username"],
        hashed_password=doc["hashed_password"],
        created_at=doc["created_at"],
        is_active=doc.get("is_active", True),
        scopes=doc.get("scopes") or ["default"],
    )


class UserAuthManager:
    """Manages user authentication with MongoDB."""

    def __init__(self):
        self.db = mongodb

    def user_exists(self, username: str) -> bool:
        return self.db.users.find_one({"username": username}) is not None

    def email_exists(self, email: str) -> bool:
        return self.db.users.find_one({"email": email}) is not None

    def create_user(self, user_data: UserRegister) -> UserInDB:
        if self.user_exists(user_data.username):
            raise ValueError(f"Username '{user_data.username}' already exists")
        if self.email_exists(user_data.email):
            raise ValueError(f"Email '{user_data.email}' already registered")

        doc = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "hashed_password": get_password_hash(user_data.password),
            "created_at": datetime.utcnow(),
            "is_active": True,
            "scopes": ["default"],
        }
        try:
            result = self.db.users.insert_one(doc)
            doc["_id"] = result.inserted_id
            return _doc_to_user(doc)
        except DuplicateKeyError:
            raise ValueError("User already exists (duplicate key)")

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        try:
            doc = self.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
        return _doc_to_user(doc) if doc else None

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        doc = self.db.users.find_one({"username": username})
        return _doc_to_user(doc) if doc else None

    def get_user_response(self, user_id: str) -> Optional[UserResponse]:
        u = self.get_user_by_id(user_id)
        if not u:
            return None
        return UserResponse(
            user_id=u.user_id,
            username=u.username,
            email=u.email,
            full_name=u.full_name,
            created_at=u.created_at,
            is_active=u.is_active,
            scopes=u.scopes,
        )

    def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        u = self.get_user_by_username(username)
        if not u or not verify_password(password, u.hashed_password) or not u.is_active:
            return None
        return u

    def update_user(self, user_id: str, updates: dict) -> bool:
        try:
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)}, {"$set": updates}
            )
            return result.modified_count > 0
        except Exception:
            return False

    def deactivate_user(self, user_id: str) -> bool:
        return self.update_user(user_id, {"is_active": False})


user_auth_manager = UserAuthManager()
