from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class FileChange:
    """Represents a single file change in a PR"""
    filename: str
    patch: str
    additions: int
    deletions: int
    status: str  # added, removed, modified, renamed
    previous_filename: Optional[str] = None  # for renamed files


@dataclass
class PullRequest:
    """Represents a GitHub Pull Request with all relevant data"""
    number: int
    title: str
    description: str
    state: str
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    base_branch: str
    head_branch: str
    author: str
    url: str
    html_url: str
    diff_url: str
    patch_url: str
    file_changes: List[FileChange]
    commits_count: int
    additions: int
    deletions: int
    changed_files: int
    
    @property
    def is_merged(self) -> bool:
        return self.merged_at is not None
    
    @property
    def is_open(self) -> bool:
        return self.state == 'open'