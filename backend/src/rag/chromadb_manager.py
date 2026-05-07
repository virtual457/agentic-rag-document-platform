"""
ChromaDB Manager - User-Isolated Vector Database

Manages ChromaDB collections for each user, providing semantic search
over their GitHub projects and documents.
"""
import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class ChromaDBManager:
    """
    Manages user-isolated ChromaDB vector databases.

    Each user gets their own ChromaDB collection at:
    chromadb_store/{username}/
    """

    def __init__(self, base_path: str = None):
        """
        Initialize ChromaDB Manager

        Args:
            base_path: Base directory for ChromaDB storage
        """
        if base_path is None:
            base_path = os.getenv("CHROMADB_PATH", "./chromadb_store")

        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True, parents=True)

        # Store active clients
        self._clients: Dict[str, chromadb.PersistentClient] = {}

    def get_client(self, username: str) -> chromadb.PersistentClient:
        """
        Get or create ChromaDB client for user

        Args:
            username: User identifier

        Returns:
            ChromaDB client instance
        """
        if username in self._clients:
            return self._clients[username]

        # Create user-specific directory
        user_path = self.base_path / username
        user_path.mkdir(exist_ok=True, parents=True)

        # Create persistent client
        client = chromadb.PersistentClient(
            path=str(user_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        self._clients[username] = client
        return client

    def get_or_create_collection(
        self,
        username: str,
        collection_name: str = "projects",
        embedding_function: Optional[Any] = None
    ) -> chromadb.Collection:
        """
        Get or create a collection for user

        Args:
            username: User identifier
            collection_name: Name of collection (default: "projects")
            embedding_function: Custom embedding function (optional)

        Returns:
            ChromaDB collection
        """
        client = self.get_client(username)

        try:
            collection = client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata={"hnsw:space": "cosine"}  # Use cosine similarity
            )
            return collection
        except Exception as e:
            raise RuntimeError(f"Failed to get/create collection: {e}")

    def add_documents(
        self,
        username: str,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        collection_name: str = "projects"
    ) -> None:
        """
        Add documents to user's collection

        Args:
            username: User identifier
            documents: List of document texts
            metadatas: List of metadata dicts
            ids: List of unique document IDs
            collection_name: Collection name
        """
        if not documents:
            raise ValueError("No documents provided")

        if len(documents) != len(metadatas) != len(ids):
            raise ValueError("documents, metadatas, and ids must have same length")

        collection = self.get_or_create_collection(username, collection_name)

        try:
            # Add in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_meta = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]

                collection.add(
                    documents=batch_docs,
                    metadatas=batch_meta,
                    ids=batch_ids
                )

            print(f"✅ Added {len(documents)} documents to {username}/{collection_name}")

        except Exception as e:
            raise RuntimeError(f"Failed to add documents: {e}")

    def query(
        self,
        username: str,
        query_texts: List[str],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        collection_name: str = "projects"
    ) -> Dict[str, Any]:
        """
        Query user's collection with semantic search

        Args:
            username: User identifier
            query_texts: List of query strings
            n_results: Number of results to return per query
            where: Metadata filters (optional)
            collection_name: Collection name

        Returns:
            Query results with documents, metadatas, distances
        """
        collection = self.get_or_create_collection(username, collection_name)

        try:
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            return results

        except Exception as e:
            raise RuntimeError(f"Failed to query collection: {e}")

    def delete_collection(self, username: str, collection_name: str = "projects") -> None:
        """
        Delete a user's collection

        Args:
            username: User identifier
            collection_name: Collection name
        """
        client = self.get_client(username)

        try:
            client.delete_collection(name=collection_name)
            print(f"🗑️  Deleted collection {username}/{collection_name}")
        except Exception as e:
            print(f"⚠️  Failed to delete collection: {e}")

    def reset_user_data(self, username: str) -> None:
        """
        Reset all data for a user (DANGEROUS!)

        Args:
            username: User identifier
        """
        user_path = self.base_path / username

        if user_path.exists():
            import shutil
            shutil.rmtree(user_path)
            print(f"🗑️  Deleted all data for user: {username}")

            # Remove from cache
            if username in self._clients:
                del self._clients[username]

    def get_collection_stats(self, username: str, collection_name: str = "projects") -> Dict[str, Any]:
        """
        Get statistics about a collection

        Args:
            username: User identifier
            collection_name: Collection name

        Returns:
            Dictionary with collection stats
        """
        try:
            collection = self.get_or_create_collection(username, collection_name)
            count = collection.count()

            return {
                "username": username,
                "collection": collection_name,
                "document_count": count,
                "path": str(self.base_path / username)
            }
        except Exception as e:
            return {
                "username": username,
                "collection": collection_name,
                "error": str(e)
            }

    def list_user_collections(self, username: str) -> List[str]:
        """
        List all collections for a user

        Args:
            username: User identifier

        Returns:
            List of collection names
        """
        client = self.get_client(username)
        collections = client.list_collections()
        return [col.name for col in collections]


# ============== Test Function ==============

def test_chromadb_manager():
    """Test ChromaDB Manager functionality"""
    print("\n" + "="*60)
    print("🧪 CHROMADB MANAGER TEST")
    print("="*60)

    # Create manager
    manager = ChromaDBManager(base_path="./test_chromadb")

    test_user = "test_user"

    # Test 1: Add documents
    print("\n📝 Test 1: Adding documents...")
    documents = [
        "Built an event-driven data pipeline using AWS Lambda, S3, and DynamoDB",
        "Developed React frontend with TypeScript and Next.js",
        "Implemented machine learning model using Python and TensorFlow"
    ]
    metadatas = [
        {"repo": "lseg-pipeline", "type": "work"},
        {"repo": "portfolio-website", "type": "project"},
        {"repo": "ml-classifier", "type": "project"}
    ]
    ids = ["doc1", "doc2", "doc3"]

    manager.add_documents(test_user, documents, metadatas, ids)

    # Test 2: Query
    print("\n🔍 Test 2: Querying...")
    results = manager.query(
        test_user,
        query_texts=["AWS backend experience"],
        n_results=2
    )

    print(f"Query: 'AWS backend experience'")
    print(f"Top result: {results['documents'][0][0][:100]}...")
    print(f"Distance: {results['distances'][0][0]:.4f}")

    # Test 3: Stats
    print("\n📊 Test 3: Collection stats...")
    stats = manager.get_collection_stats(test_user)
    print(json.dumps(stats, indent=2))

    # Cleanup
    print("\n🗑️  Cleaning up...")
    manager.reset_user_data(test_user)

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_chromadb_manager()
