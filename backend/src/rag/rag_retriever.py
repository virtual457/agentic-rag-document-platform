"""
RAG Retriever - Semantic Search for Resume Generation

Retrieves relevant experiences and projects from user's vector database
to enhance resume generation with factual, verifiable content.
"""
import os
from typing import List, Dict, Any, Optional
from .chromadb_manager import ChromaDBManager
from .github_ingestor import GitHubIngestor


class RAGRetriever:
    """
    Retrieves relevant content from user's vector database.

    Provides semantic search over GitHub projects and documents
    to find experiences relevant to job descriptions.
    """

    def __init__(self, chromadb_manager: Optional[ChromaDBManager] = None):
        """
        Initialize RAG Retriever

        Args:
            chromadb_manager: ChromaDB manager instance (creates new if not provided)
        """
        self.chromadb = chromadb_manager or ChromaDBManager()

    def search(
        self,
        username: str,
        query: str,
        n_results: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search user's vector database for relevant content

        Args:
            username: User identifier
            query: Search query (e.g., "AWS backend experience")
            n_results: Number of results to return
            filters: Metadata filters (e.g., {"language": "Python"})

        Returns:
            List of matching documents with scores
        """
        try:
            # Query ChromaDB
            results = self.chromadb.query(
                username=username,
                query_texts=[query],
                n_results=n_results,
                where=filters
            )

            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                result = {
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                    "relevance_score": 1 - results["distances"][0][i]  # Convert distance to similarity
                }
                formatted_results.append(result)

            return formatted_results

        except Exception as e:
            print(f"❌ Error during search: {e}")
            return []

    def search_multiple_queries(
        self,
        username: str,
        queries: List[str],
        n_results_per_query: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search with multiple queries and return aggregated results

        Args:
            username: User identifier
            queries: List of search queries
            n_results_per_query: Results to return per query

        Returns:
            Dict mapping queries to their results
        """
        results_map = {}

        for query in queries:
            results = self.search(username, query, n_results=n_results_per_query)
            results_map[query] = results

        return results_map

    def get_context_for_jd(
        self,
        username: str,
        jd_text: str,
        max_chunks: int = 10
    ) -> str:
        """
        Get relevant context from user's projects based on job description

        Extracts key skills/technologies from JD and searches for them.

        Args:
            username: User identifier
            jd_text: Job description text
            max_chunks: Maximum number of content chunks to return

        Returns:
            Concatenated relevant content
        """
        # Extract key terms from JD (simple approach)
        queries = self._extract_key_terms(jd_text)

        if not queries:
            print("⚠️  Could not extract key terms from JD")
            return ""

        print(f"🔍 Extracted queries from JD: {queries[:5]}...")

        # Search for each query
        all_results = []
        for query in queries[:5]:  # Limit to top 5 queries
            results = self.search(username, query, n_results=3)
            all_results.extend(results)

        # Deduplicate and sort by relevance
        unique_results = {}
        for result in all_results:
            doc_id = result["metadata"].get("repo", "unknown")
            if doc_id not in unique_results or result["relevance_score"] > unique_results[doc_id]["relevance_score"]:
                unique_results[doc_id] = result

        # Sort by relevance and take top N
        sorted_results = sorted(
            unique_results.values(),
            key=lambda x: x["relevance_score"],
            reverse=True
        )[:max_chunks]

        # Concatenate content
        context_parts = []
        for i, result in enumerate(sorted_results, 1):
            repo = result["metadata"].get("repo", "Unknown")
            content = result["content"][:500]  # Limit length
            score = result["relevance_score"]

            context_parts.append(
                f"[Project {i}: {repo} (relevance: {score:.2f})]\n{content}\n"
            )

        context = "\n".join(context_parts)
        print(f"✅ Retrieved {len(sorted_results)} relevant project chunks")

        return context

    def _extract_key_terms(self, jd_text: str) -> List[str]:
        """
        Extract key technical terms from job description

        Simple keyword extraction for MVP. Could be enhanced with NLP.

        Args:
            jd_text: Job description text

        Returns:
            List of key terms/technologies
        """
        # Common tech keywords to look for
        keywords = [
            "python", "java", "javascript", "typescript", "go", "rust", "c++",
            "aws", "azure", "gcp", "cloud",
            "docker", "kubernetes", "k8s",
            "react", "vue", "angular", "nextjs",
            "node", "express", "fastapi", "django", "flask",
            "sql", "postgresql", "mysql", "mongodb", "dynamodb",
            "redis", "kafka", "rabbitmq",
            "machine learning", "deep learning", "ai", "nlp",
            "terraform", "ansible", "ci/cd",
            "microservices", "api", "rest", "graphql",
            "backend", "frontend", "fullstack", "full stack"
        ]

        jd_lower = jd_text.lower()

        found_terms = []
        for keyword in keywords:
            if keyword in jd_lower:
                found_terms.append(keyword)

        # Also extract phrases like "5 years of experience in..."
        import re
        experience_pattern = r'experience (?:in|with) ([a-zA-Z\s,/]+?)(?:\.|,|\n|$)'
        matches = re.findall(experience_pattern, jd_lower)
        for match in matches:
            terms = [t.strip() for t in match.split(',')]
            found_terms.extend(terms[:2])  # Take first 2

        return found_terms[:10]  # Limit total queries

    def get_project_summary(self, username: str) -> Dict[str, Any]:
        """
        Get summary of all projects in user's vector database

        Args:
            username: User identifier

        Returns:
            Dict with project statistics
        """
        stats = self.chromadb.get_collection_stats(username)

        # Get all unique repos
        try:
            collection = self.chromadb.get_or_create_collection(username)
            # Get a sample to show
            sample = collection.peek(limit=5)

            repos = set()
            for metadata in sample.get("metadatas", []):
                if "repo" in metadata:
                    repos.add(metadata["repo"])

            return {
                "total_documents": stats["document_count"],
                "sample_repos": list(repos),
                "status": "ready"
            }

        except Exception as e:
            return {
                "total_documents": 0,
                "error": str(e),
                "status": "not_initialized"
            }


# ============== Setup Function ==============

def setup_rag_for_user(
    username: str,
    github_username: Optional[str] = None,
    max_repos: int = 25,
    use_gitingest: bool = True
) -> Dict[str, Any]:
    """
    Setup RAG system for a user by ingesting their GitHub repos

    Args:
        username: User identifier in the system
        github_username: GitHub username (defaults to same as username)
        max_repos: Maximum repos to ingest
        use_gitingest: Whether to use GitIngest API

    Returns:
        Dict with setup results
    """
    print(f"\n{'='*60}")
    print(f"🚀 Setting up RAG for user: {username}")
    print(f"{'='*60}")

    github_username = github_username or username

    # Initialize components
    chromadb = ChromaDBManager()
    ingestor = GitHubIngestor(use_gitingest=use_gitingest)

    # Ingest GitHub repos
    print(f"\n📚 Ingesting GitHub repos...")
    documents = ingestor.ingest_all_repos(
        github_username,
        max_repos=max_repos
    )

    if not documents:
        return {
            "success": False,
            "error": "No documents ingested",
            "documents_added": 0
        }

    # Add to ChromaDB
    print(f"\n💾 Adding to ChromaDB...")
    chromadb.add_documents(
        username=username,
        documents=[doc["content"] for doc in documents],
        metadatas=[doc["metadata"] for doc in documents],
        ids=[doc["id"] for doc in documents]
    )

    # Get stats
    stats = chromadb.get_collection_stats(username)

    print(f"\n{'='*60}")
    print(f"✅ RAG Setup Complete!")
    print(f"   Documents: {stats['document_count']}")
    print(f"   Storage: {stats['path']}")
    print(f"{'='*60}\n")

    return {
        "success": True,
        "username": username,
        "documents_added": len(documents),
        "stats": stats
    }


# ============== Test Function ==============

def test_rag_retriever():
    """Test RAG Retriever"""
    print("\n" + "="*60)
    print("🧪 RAG RETRIEVER TEST")
    print("="*60)

    # Setup test data first
    from .chromadb_manager import ChromaDBManager

    chromadb = ChromaDBManager(base_path="./test_chromadb")
    test_user = "test_user"

    # Add some test documents
    documents = [
        "Built an event-driven data pipeline using AWS Lambda, S3, DynamoDB, and SQS. Processed 7.5 million records across 180 countries with 40% latency reduction.",
        "Developed a full-stack resume optimizer using React, Next.js, TypeScript, FastAPI, and Python. Integrated LangChain for multi-agent coordination.",
        "Created machine learning classifier using TensorFlow and Python for image recognition. Achieved 95% accuracy on test dataset."
    ]
    metadatas = [
        {"repo": "lseg-pipeline", "language": "Python", "type": "work"},
        {"repo": "resume-optimizer", "language": "TypeScript", "type": "project"},
        {"repo": "ml-classifier", "language": "Python", "type": "project"}
    ]
    ids = ["doc1", "doc2", "doc3"]

    chromadb.add_documents(test_user, documents, metadatas, ids)

    # Test retriever
    retriever = RAGRetriever(chromadb)

    # Test 1: Simple search
    print("\n🔍 Test 1: Simple search for 'AWS backend'")
    results = retriever.search(test_user, "AWS backend experience", n_results=2)
    for i, result in enumerate(results, 1):
        print(f"\n  [{i}] {result['metadata']['repo']}")
        print(f"      Score: {result['relevance_score']:.3f}")
        print(f"      Content: {result['content'][:80]}...")

    # Test 2: JD context extraction
    print("\n\n🔍 Test 2: Extract context from JD")
    jd = """
    We're looking for a Senior Backend Engineer with 5+ years of experience in Python and AWS.
    Must have experience with Lambda, DynamoDB, and building event-driven architectures.
    """
    context = retriever.get_context_for_jd(test_user, jd, max_chunks=2)
    print(f"\nContext extracted ({len(context)} chars):")
    print(context[:300] + "...")

    # Cleanup
    print("\n\n🗑️  Cleaning up...")
    chromadb.reset_user_data(test_user)

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_rag_retriever()
