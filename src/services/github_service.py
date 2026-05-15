import aiohttp
from typing import Optional, List
from src.types import Release, ReleaseAsset
from src.logger import logger

class GitHubService:
    """GitHub API Service for fetching releases"""

    def __init__(self, owner: str, repo: str, token: Optional[str] = None):
        self.owner = owner
        self.repo = repo
        self.token = token
        self.base_url = "https://api.github.com"

    async def get_latest_release(self, include_pre_releases: bool = False) -> Optional[Release]:
        """Fetch the latest release"""
        try:
            releases = await self.get_releases()

            if not releases:
                logger.warning("No releases found")
                return None

            filtered_releases = releases
            if not include_pre_releases:
                filtered_releases = [r for r in releases if not r.prerelease]

            if not filtered_releases:
                logger.warning("No stable releases found")
                return None

            return filtered_releases[0]
        except Exception as e:
            logger.error(f"Failed to get latest release: {e}")
            raise

    async def get_release_by_tag(self, tag: str) -> Optional[Release]:
        """Fetch a specific release by tag"""
        try:
            logger.debug(f"Fetching specific release with tag: {tag}")
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/releases/tags/{tag}"
            headers = self._get_headers()

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 404:
                        logger.warning(f"Release tag '{tag}' not found")
                        return None

                    if response.status != 200:
                        logger.error(f"GitHub API error: {response.status}")
                        return None

                    data = await response.json()
                    return self._map_github_release(data)
        except Exception as e:
            logger.error(f"Failed to fetch release with tag '{tag}': {e}")
            raise

    async def get_releases(self, limit: int = 10) -> List[Release]:
        """Fetch releases from GitHub"""
        try:
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/releases?per_page={limit}"
            headers = self._get_headers()

            logger.debug(f"Fetching releases from {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"GitHub API error: {response.status}")
                        return []

                    data = await response.json()
                    return [self._map_github_release(r) for r in data]
        except Exception as e:
            logger.error(f"Failed to fetch releases from GitHub: {e}")
            raise

    def _map_github_release(self, gh_release: dict) -> Release:
        """Map GitHub API response to Release object"""
        assets = [
            ReleaseAsset(
                id=asset['id'],
                name=asset['name'],
                size=asset['size'],
                download_url=asset['browser_download_url']
            )
            for asset in gh_release.get('assets', [])
        ]

        return Release(
            id=gh_release['id'],
            tag_name=gh_release['tag_name'],
            name=gh_release.get('name') or gh_release['tag_name'],
            body=gh_release.get('body') or '',
            draft=gh_release.get('draft', False),
            prerelease=gh_release.get('prerelease', False),
            created_at=gh_release.get('created_at', ''),
            published_at=gh_release.get('published_at', ''),
            html_url=gh_release.get('html_url', ''),
            assets=assets
        )

    def _get_headers(self) -> dict:
        """Get HTTP headers for GitHub API"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'discord-release-bot-python'
        }

        if self.token:
            headers['Authorization'] = f'token {self.token}'

        return headers
