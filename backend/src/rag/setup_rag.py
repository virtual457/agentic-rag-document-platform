"""
RAG Setup Script

Run this script to initialize RAG system for a user by ingesting their GitHub repositories.

Usage:
    python setup_rag.py --username chandan --github virtual457
    python setup_rag.py --username chandan --github virtual457 --max-repos 10
"""
import argparse
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rag.rag_retriever import setup_rag_for_user
from src.rag.chromadb_manager import ChromaDBManager
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Setup RAG system by ingesting GitHub repositories"
    )
    parser.add_argument(
        "--username",
        required=True,
        help="User identifier in the system"
    )
    parser.add_argument(
        "--github",
        help="GitHub username (defaults to same as username)"
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=25,
        help="Maximum number of repos to ingest (default: 25)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing data before ingesting"
    )
    parser.add_argument(
        "--use-github-api",
        action="store_true",
        help="Use GitHub API instead of GitIngest (requires GITHUB_TOKEN)"
    )

    args = parser.parse_args()

    # Reset if requested
    if args.reset:
        print(f"\n⚠️  Resetting existing data for {args.username}...")
        chromadb = ChromaDBManager()
        chromadb.reset_user_data(args.username)
        print("✅ Data reset complete")

    # Setup RAG
    result = setup_rag_for_user(
        username=args.username,
        github_username=args.github,
        max_repos=args.max_repos,
        use_gitingest=not args.use_github_api
    )

    if result["success"]:
        print("\n" + "="*60)
        print("🎉 SUCCESS!")
        print("="*60)
        print(f"User: {result['username']}")
        print(f"Documents added: {result['documents_added']}")
        print(f"Total in database: {result['stats']['document_count']}")
        print(f"Storage path: {result['stats']['path']}")
        print("="*60)
        print("\n✅ RAG system is ready!")
        print("   You can now use semantic search in resume generation.")
        print("\nNext steps:")
        print("  1. Generate a resume with RAG-enhanced context")
        print("  2. The system will automatically search your projects")
        print("  3. Resumes will include verifiable project details")
        print()
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ SETUP FAILED")
        print("="*60)
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Documents added: {result.get('documents_added', 0)}")
        print("="*60)
        print("\nTroubleshooting:")
        print("  - Check GitHub username is correct")
        print("  - Ensure repositories are public")
        print("  - Try with --use-github-api if GitIngest fails")
        print("  - Check GITHUB_TOKEN if using GitHub API")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
