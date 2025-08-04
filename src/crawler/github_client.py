import os
import re
import requests
from typing import Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse
import time

from .models import PullRequest, FileChange


class GitHubClient:
    """Client for interacting with GitHub API to fetch PR data"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN environment variable or pass token to constructor.")
        
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        self.base_url = 'https://api.github.com'
        self._last_request_time = 0
        self._min_request_interval = 0.5  # Rate limiting: max 2 requests per second
    
    def _parse_pr_url(self, pr_url: str) -> Tuple[str, str, int]:
        """
        Parse GitHub PR URL to extract owner, repo, and PR number
        
        Supports formats:
        - https://github.com/owner/repo/pull/123
        - github.com/owner/repo/pull/123
        - owner/repo/pull/123
        """
        pr_url = pr_url.strip()
        
        # Try to parse as URL
        if pr_url.startswith('http://') or pr_url.startswith('https://'):
            parsed = urlparse(pr_url)
            path = parsed.path.strip('/')
        else:
            # Handle github.com/owner/repo/pull/123 or owner/repo/pull/123
            if pr_url.startswith('github.com/'):
                path = pr_url[11:]
            else:
                path = pr_url
        
        # Extract owner, repo, and PR number
        match = re.match(r'([^/]+)/([^/]+)/pull/(\d+)', path)
        if not match:
            raise ValueError(f"Invalid PR URL format: {pr_url}")
        
        owner, repo, pr_number = match.groups()
        return owner, repo, int(pr_number)
    
    def _rate_limit(self):
        """Simple rate limiting to avoid hitting GitHub API limits"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time
        if time_since_last_request < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last_request)
        self._last_request_time = time.time()
    
    def _make_request(self, endpoint: str) -> dict:
        """Make a rate-limited request to GitHub API"""
        self._rate_limit()
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url)
        
        if response.status_code == 404:
            raise ValueError(f"Resource not found: {url}")
        elif response.status_code == 401:
            raise ValueError("Invalid GitHub token")
        elif response.status_code == 403:
            # Check if it's rate limiting
            if 'X-RateLimit-Remaining' in response.headers and response.headers['X-RateLimit-Remaining'] == '0':
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                wait_time = reset_time - time.time()
                raise RuntimeError(f"GitHub API rate limit exceeded. Try again in {wait_time:.0f} seconds.")
            raise ValueError("Access forbidden. Check your GitHub token permissions.")
        
        response.raise_for_status()
        return response.json()
    
    def fetch_pr(self, pr_url: str) -> PullRequest:
        """
        Fetch pull request data from GitHub
        
        Args:
            pr_url: GitHub PR URL
            
        Returns:
            PullRequest object with all PR data
        """
        owner, repo, pr_number = self._parse_pr_url(pr_url)
        
        # Fetch PR metadata
        pr_data = self._make_request(f"/repos/{owner}/{repo}/pulls/{pr_number}")
        
        # Fetch file changes
        files_data = self._make_request(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
        
        # Convert file changes
        file_changes = []
        for file in files_data:
            file_change = FileChange(
                filename=file['filename'],
                patch=file.get('patch', ''),
                additions=file['additions'],
                deletions=file['deletions'],
                status=file['status'],
                previous_filename=file.get('previous_filename')
            )
            file_changes.append(file_change)
        
        # Create PullRequest object
        pr = PullRequest(
            number=pr_data['number'],
            title=pr_data['title'],
            description=pr_data.get('body', ''),
            state=pr_data['state'],
            created_at=datetime.fromisoformat(pr_data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(pr_data['updated_at'].replace('Z', '+00:00')),
            merged_at=datetime.fromisoformat(pr_data['merged_at'].replace('Z', '+00:00')) if pr_data['merged_at'] else None,
            base_branch=pr_data['base']['ref'],
            head_branch=pr_data['head']['ref'],
            author=pr_data['user']['login'],
            url=pr_data['url'],
            html_url=pr_data['html_url'],
            diff_url=pr_data['diff_url'],
            patch_url=pr_data['patch_url'],
            file_changes=file_changes,
            commits_count=pr_data['commits'],
            additions=pr_data['additions'],
            deletions=pr_data['deletions'],
            changed_files=pr_data['changed_files']
        )
        
        return pr