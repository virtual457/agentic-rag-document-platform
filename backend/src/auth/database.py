"""MongoDB database connection and management (lazy singleton)."""
import os
from typing import Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

load_dotenv()


class MongoDB:
    """MongoDB connection manager. Lazy: connects on first property access."""

    _instance = None
    _client: Optional[MongoClient] = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDB, cls).__new__(cls)
        return cls._instance

    def _uri(self) -> str:
        return os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or ""

    def _db_name(self) -> str:
        return os.getenv("MONGO_DB") or os.getenv("MONGODB_DB_NAME") or "docintel"

    def connect(self):
        uri = self._uri()
        if not uri:
            raise ValueError("MONGO_URI (or MONGODB_URI) not set in environment variables")
        if self._client is None:
            self._client = MongoClient(uri)
            try:
                self._client.admin.command("ping")
            except ConnectionFailure as e:
                raise ValueError(f"MongoDB ping failed: {e}")
            self._db = self._client[self._db_name()]
            self._setup_indexes()

    def _setup_indexes(self):
        try:
            self._db.users.create_index("username", unique=True)
            self._db.users.create_index("email", unique=True)
        except Exception:
            pass

    @property
    def db(self):
        if self._db is None:
            self.connect()
        return self._db

    @property
    def users(self):
        return self.db.users

    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None


mongodb = MongoDB()  # Lazy — no connection until first property access.
