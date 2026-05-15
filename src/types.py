from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class ReleaseAsset:
    """GitHub Release Asset"""
    id: int
    name: str
    size: int
    download_url: str

    def format_size(self) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024
        return f"{self.size:.1f} TB"

@dataclass
class Release:
    """GitHub Release"""
    id: int
    tag_name: str
    name: str
    body: str
    draft: bool
    prerelease: bool
    created_at: str
    published_at: str
    html_url: str
    assets: List[ReleaseAsset]

    def __post_init__(self):
        """Ensure published_at has a value"""
        if not self.published_at:
            self.published_at = self.created_at
