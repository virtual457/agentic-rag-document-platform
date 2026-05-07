"""
RAG System Test Script

Tests the complete RAG pipeline:
1. GitHub ingestion
2. ChromaDB storage
3. Semantic search
4. Resume generation with RAG

Usage:
    python test_rag.py --username chandan --github virtual457
"""
import argparse
import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from src.rag.chromadb_manager import ChromaDBManager
from src.rag.github_ingestor import GitHubIngestor
from src.rag.rag_retriever import RAGRetriever, setup_rag_for_user
from dotenv import load_dotenv

load_dotenv()


def test_chromadb():
    """Test 1: ChromaDB Manager"""
    print("\n" + "="*60)
    print("TEST 1: CHROMADB MANAGER")
    print("="*60)

    manager = ChromaDBManager()

    # Test user
    test_user = "test_user_rag"

    # Add test documents
    print("\n📝 Adding test documents...")
    documents = [
        "Built AWS Lambda serverless backend with Python, DynamoDB, and S3",
        "Developed React TypeScript frontend with Next.js and Tailwind CSS",
        "Implemented CI/CD pipeline using GitHub Actions and Docker",
    ]
    metadatas = [
        {"repo": "aws-backend", "language": "Python"},
        {"repo": "react-app", "language": "TypeScript"},
        {"repo": "devops-tools", "language": "Shell"},
    ]
    ids = ["doc1", "doc2", "doc3"]

    manager.add_documents(test_user, documents, metadatas, ids)

    # Query
    print("\n🔍 Testing search...")
    results = manager.query(
        test_user,
        query_texts=["AWS serverless Python"],
        n_results=2
    )

    print(f"Query: 'AWS serverless Python'")
    print(f"Results: {len(results['documents'][0])}")
    for i, doc in enumerate(results["documents"][0]):
        distance = results["distances"][0][i]
        print(f"  [{i+1}] {doc[:60]}... (distance: {distance:.3f})")

    # Stats
    stats = manager.get_collection_stats(test_user)
    print(f"\n📊 Stats: {stats['document_count']} documents")

    # Cleanup
    print("\n🗑️  Cleaning up...")
    manager.reset_user_data(test_user)

    print("✅ Test 1 passed!\n")


def test_github_ingestor():
    """Test 2: GitHub Ingestor"""
    print("\n" + "="*60)
    print("TEST 2: GITHUB INGESTOR")
    print("="*60)

    ingestor = GitHubIngestor(use_gitingest=True)

    # Fetch repos
    print("\n📚 Fetching repos for 'virtual457'...")
    repos = ingestor.fetch_repos("virtual457")

    if repos:
        print(f"✅ Found {len(repos)} repositories")
        print(f"\nFirst 3 repos:")
        for repo in repos[:3]:
            print(f"  - {repo['name']}: {repo['description'][:50] if repo['description'] else 'No description'}...")

        # Extract content from first repo
        print(f"\n📖 Extracting content from: {repos[0]['name']}")
        content = ingestor.extract_repo_content(repos[0]['url'])
        print(f"✅ Extracted {len(content)} characters")
        print(f"Preview: {content[:200]}...")

        print("\n✅ Test 2 passed!\n")
    else:
        print("⚠️  No repos found or error occurred\n")


def test_rag_retriever():
    """Test 3: RAG Retriever"""
    print("\n" + "="*60)
    print("TEST 3: RAG RETRIEVER")
    print("="*60)

    # Setup test data
    chromadb = ChromaDBManager()
    test_user = "test_user_retriever"

    documents = [
        "Built event-driven data pipeline using AWS Lambda, S3, DynamoDB, and SQS. Processed 7.5 million records across 180 countries.",
        "Developed full-stack application with React, Next.js, TypeScript, FastAPI, and PostgreSQL. Deployed on AWS with Docker.",
        "Created machine learning model using Python, TensorFlow, and scikit-learn. Achieved 95% accuracy on image classification."
    ]
    metadatas = [
        {"repo": "lseg-pipeline", "language": "Python", "type": "work"},
        {"repo": "fullstack-app", "language": "TypeScript", "type": "project"},
        {"repo": "ml-model", "language": "Python", "type": "project"}
    ]
    ids = ["doc1", "doc2", "doc3"]

    chromadb.add_documents(test_user, documents, metadatas, ids)

    # Test retriever
    retriever = RAGRetriever(chromadb)

    # Test search
    print("\n🔍 Testing semantic search...")
    results = retriever.search(test_user, "AWS backend Python experience", n_results=2)

    for i, result in enumerate(results, 1):
        print(f"\n  [{i}] {result['metadata']['repo']}")
        print(f"      Relevance: {result['relevance_score']:.3f}")
        print(f"      Content: {result['content'][:80]}...")

    # Test JD context extraction
    print("\n\n🔍 Testing JD context extraction...")
    jd = """
    Senior Backend Engineer role. Must have 5+ years of experience with Python, AWS Lambda, DynamoDB.
    Experience with event-driven architectures and microservices required.
    """

    context = retriever.get_context_for_jd(test_user, jd, max_chunks=2)
    print(f"✅ Extracted context ({len(context)} chars)")
    print(f"Preview:\n{context[:300]}...")

    # Cleanup
    print("\n\n🗑️  Cleaning up...")
    chromadb.reset_user_data(test_user)

    print("\n✅ Test 3 passed!\n")


def test_full_setup(username: str, github_username: str, max_repos: int = 5):
    """Test 4: Full RAG Setup"""
    print("\n" + "="*60)
    print("TEST 4: FULL RAG SETUP")
    print("="*60)

    print(f"\n🚀 Setting up RAG for {username} (GitHub: {github_username})")
    print(f"   Max repos: {max_repos}")

    result = setup_rag_for_user(
        username=username,
        github_username=github_username,
        max_repos=max_repos,
        use_gitingest=True
    )

    if result["success"]:
        print("\n✅ Test 4 passed!")
        print(f"   Documents added: {result['documents_added']}")
        print(f"   Total documents: {result['stats']['document_count']}")

        # Test search
        print("\n🔍 Testing search on ingested data...")
        retriever = RAGRetriever()
        results = retriever.search(username, "Python backend AWS", n_results=3)

        print(f"   Found {len(results)} results:")
        for i, result in enumerate(results, 1):
            print(f"   [{i}] {result['metadata'].get('repo', 'unknown')}: {result['relevance_score']:.3f}")

    else:
        print(f"\n❌ Test 4 failed: {result.get('error', 'Unknown error')}")


def main():
    parser = argparse.ArgumentParser(description="Test RAG system")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--chromadb", action="store_true", help="Test ChromaDB")
    parser.add_argument("--github", action="store_true", help="Test GitHub ingestor")
    parser.add_argument("--retriever", action="store_true", help="Test RAG retriever")
    parser.add_argument("--setup", action="store_true", help="Test full setup")
    parser.add_argument("--username", default="test_user", help="Username for setup test")
    parser.add_argument("--github-username", default="virtual457", help="GitHub username")
    parser.add_argument("--max-repos", type=int, default=5, help="Max repos for setup")

    args = parser.parse_args()

    # If no specific test, run all
    if not any([args.chromadb, args.github, args.retriever, args.setup]):
        args.all = True

    print("\n" + "="*60)
    print("🧪 RAG SYSTEM TEST SUITE")
    print("="*60)

    try:
        if args.all or args.chromadb:
            test_chromadb()

        if args.all or args.github:
            test_github_ingestor()

        if args.all or args.retriever:
            test_rag_retriever()

        if args.setup:
            test_full_setup(args.username, args.github_username, args.max_repos)

        print("\n" + "="*60)
        print("🎉 ALL TESTS COMPLETED!")
        print("="*60)
        print()

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
