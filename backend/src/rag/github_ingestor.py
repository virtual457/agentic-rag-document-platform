"""
GitHub Repository Ingestor

Fetches GitHub repositories and extracts content for RAG system.
Supports two methods:
1. GitIngest API (fast, no auth needed)
2. GitHub API (more control, requires token)
"""
import os
import requests
import time
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import re


class GitHubIngestor:
    """
    Ingests GitHub repositories for RAG system.

    Extracts:
    - README files
    - Documentation files
    - Code comments and docstrings
    - Project descriptions
    """

    def __init__(self, github_token: Optional[str] = None, use_gitingest: bool = True):
        """
        Initialize GitHub Ingestor

        Args:
            github_token: GitHub Personal Access Token (for GitHub API method)
            use_gitingest: Whether to use GitIngest API (default: True, faster)
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.use_gitingest = use_gitingest

        if not use_gitingest and not self.github_token:
            raise ValueError("GitHub token required when not using GitIngest")

        self.session = requests.Session()
        if self.github_token:
            self.session.headers.update({
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            })

    def fetch_repos(self, username: str) -> List[Dict[str, Any]]:
        """
        Fetch list of user's public repositories

        Args:
            username: GitHub username

        Returns:
            List of repository metadata dicts
        """
        if self.use_gitingest:
            return self._fetch_repos_gitingest(username)
        else:
            return self._fetch_repos_github_api(username)

    def _fetch_repos_github_api(self, username: str) -> List[Dict[str, Any]]:
        """Fetch repos using GitHub API"""
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": 100, "sort": "updated"}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            repos = response.json()

            return [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description", ""),
                    "url": repo["html_url"],
                    "language": repo.get("language", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "updated_at": repo.get("updated_at", "")
                }
                for repo in repos
                if not repo.get("fork", False)  # Skip forked repos
            ]

        except Exception as e:
            print(f"❌ Error fetching repos: {e}")
            return []

    def _fetch_repos_gitingest(self, username: str) -> List[Dict[str, Any]]:
        """Fetch repos using GitIngest API (simpler, no auth)"""
        # GitIngest doesn't have a user repo list endpoint
        # We'll need to use GitHub API for this part even with GitIngest
        url = f"https://api.github.com/users/{username}/repos"
        params = {"per_page": 100, "sort": "updated"}

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            repos = response.json()

            return [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description", ""),
                    "url": repo["html_url"],
                    "language": repo.get("language", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "updated_at": repo.get("updated_at", "")
                }
                for repo in repos
                if not repo.get("fork", False)
            ]

        except Exception as e:
            print(f"❌ Error fetching repos: {e}")
            return []

    def extract_repo_content(self, repo_url: str) -> str:
        """
        Extract content from a repository

        Args:
            repo_url: Repository URL (e.g., https://github.com/user/repo)

        Returns:
            Extracted text content
        """
        if self.use_gitingest:
            return self._extract_via_gitingest(repo_url)
        else:
            return self._extract_via_github_api(repo_url)

    def _extract_via_gitingest(self, repo_url: str) -> str:
        """Extract repo content using GitIngest API"""
        # GitIngest API endpoint
        gitingest_url = "https://gitingest.com/api/ingest"

        try:
            response = requests.post(
                gitingest_url,
                json={"url": repo_url},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                return content
            else:
                print(f"⚠️  GitIngest failed for {repo_url}: {response.status_code}")
                return ""

        except requests.Timeout:
            print(f"⏱️  Timeout fetching {repo_url}")
            return ""
        except Exception as e:
            print(f"❌ Error with GitIngest for {repo_url}: {e}")
            return ""

    def _extract_via_github_api(self, repo_url: str) -> str:
        """Extract repo content using GitHub API"""
        # Parse repo URL
        match = re.match(r"https://github.com/([^/]+)/([^/]+)", repo_url)
        if not match:
            print(f"❌ Invalid GitHub URL: {repo_url}")
            return ""

        owner, repo = match.groups()
        repo = repo.replace(".git", "")

        content_parts = []

        # Get README
        readme = self._fetch_readme(owner, repo)
        if readme:
            content_parts.append(f"# README\n\n{readme}")

        # Get repo description
        repo_info = self._fetch_repo_info(owner, repo)
        if repo_info:
            content_parts.append(f"# Description\n\n{repo_info}")

        return "\n\n".join(content_parts)

    def _fetch_readme(self, owner: str, repo: str) -> str:
        """Fetch README content"""
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Content is base64 encoded
                import base64
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
            return ""
        except Exception as e:
            print(f"⚠️  Could not fetch README for {owner}/{repo}: {e}")
            return ""

    def _fetch_repo_info(self, owner: str, repo: str) -> str:
        """Fetch basic repo info"""
        url = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                description = data.get("description", "")
                topics = data.get("topics", [])
                language = data.get("language", "")

                info_parts = []
                if description:
                    info_parts.append(f"Description: {description}")
                if language:
                    info_parts.append(f"Language: {language}")
                if topics:
                    info_parts.append(f"Topics: {', '.join(topics)}")

                return "\n".join(info_parts)
            return ""
        except Exception as e:
            print(f"⚠️  Could not fetch repo info for {owner}/{repo}: {e}")
            return ""

    def ingest_all_repos(
        self,
        username: str,
        max_repos: Optional[int] = None,
        min_stars: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Ingest all repositories for a user

        Args:
            username: GitHub username
            max_repos: Maximum number of repos to ingest (None = all)
            min_stars: Minimum stars required

        Returns:
            List of ingested documents with metadata
        """
        print(f"\n{'='*60}")
        print(f"📚 Ingesting GitHub repos for {username}")
        print(f"{'='*60}")

        # Fetch repo list
        print("\n🔍 Fetching repository list...")
        repos = self.fetch_repos(username)

        if not repos:
            print("❌ No repositories found")
            return []

        print(f"✅ Found {len(repos)} repositories")

        # Filter by stars
        repos = [r for r in repos if r["stars"] >= min_stars]
        if len(repos) < len(self.fetch_repos(username)):
            print(f"⭐ Filtered to {len(repos)} repos with {min_stars}+ stars")

        # Limit number
        if max_repos and len(repos) > max_repos:
            repos = repos[:max_repos]
            print(f"📊 Limited to {max_repos} most recent repos")

        # Ingest each repo
        documents = []
        for i, repo in enumerate(repos, 1):
            print(f"\n[{i}/{len(repos)}] 📦 {repo['name']}")

            try:
                content = self.extract_repo_content(repo["url"])

                if content:
                    doc = {
                        "content": content,
                        "metadata": {
                            "repo": repo["name"],
                            "full_name": repo["full_name"],
                            "description": repo["description"],
                            "url": repo["url"],
                            "language": repo["language"],
                            "stars": repo["stars"],
                            "type": "github_repo"
                        },
                        "id": f"repo_{repo['full_name'].replace('/', '_')}"
                    }
                    documents.append(doc)
                    print(f"   ✅ Extracted {len(content)} chars")
                else:
                    print(f"   ⚠️  No content extracted")

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                continue

        print(f"\n{'='*60}")
        print(f"✅ Ingested {len(documents)} repositories")
        print(f"{'='*60}\n")

        return documents


# ============== Test Function ==============

def test_github_ingestor():
    """Test GitHub Ingestor"""
    print("\n" + "="*60)
    print("🧪 GITHUB INGESTOR TEST")
    print("="*60)

    # Test with GitIngest
    ingestor = GitHubIngestor(use_gitingest=True)

    # Fetch repos
    print("\n📝 Fetching repos for 'virtual457'...")
    repos = ingestor.fetch_repos("virtual457")
    print(f"Found {len(repos)} repos")

    if repos:
        print(f"\nFirst repo: {repos[0]['name']}")
        print(f"Description: {repos[0]['description']}")

        # Extract content from first repo
        print(f"\n📖 Extracting content from {repos[0]['name']}...")
        content = ingestor.extract_repo_content(repos[0]['url'])
        print(f"Extracted {len(content)} characters")
        print(f"Preview: {content[:200]}...")

    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_github_ingestor()
