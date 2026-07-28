from discord import Embed, Color
from datetime import datetime
from src.types import Release
from src.logger import logger

class FormatterService:
    """Service for formatting Discord embeds"""

    def __init__(self, app_name: str):
        self.app_name = app_name
        self.VIOLET_COLOR = Color.from_rgb(123, 44, 191)  # #7B2CBF
        self.MAX_FIELD_LENGTH = 1024

    def create_release_embed(self, release: Release) -> Embed:
        """Create a Discord embed for a release"""
        logger.debug(f"Creating embed for release {release.tag_name}")

        release_type = "Beta" if release.prerelease else "Stable"
        embed = Embed(
            title=f"{self.app_name} {release_type} - {release.tag_name}",
            url=release.html_url,
            color=Color.orange() if release.prerelease else self.VIOLET_COLOR,
            description=""
        )

        # Version and Release Date in one row (inline)
        embed.add_field(
            name="Version",
            value=release.tag_name,
            inline=True
        )

        if release.published_at:
            try:
                date_obj = datetime.fromisoformat(release.published_at.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime("%d. %b %Y")
                embed.add_field(
                    name="Released",
                    value=formatted_date,
                    inline=True
                )
            except Exception as e:
                logger.warning(f"Failed to parse release date: {e}")

        # Changelog section
        if release.body:
            changelog = release.body.strip()
            if len(changelog) > self.MAX_FIELD_LENGTH:
                chunks = self._split_text(changelog, self.MAX_FIELD_LENGTH)
                embed.add_field(
                    name="What's New",
                    value=chunks[0] if chunks else "No changelog available",
                    inline=False
                )
                if len(chunks) > 1:
                    embed.add_field(
                        name="More Details",
                        value=f"[View full changelog on GitHub]({release.html_url})",
                        inline=False
                    )
            else:
                embed.add_field(
                    name="What's New",
                    value=changelog,
                    inline=False
                )

        # Downloads section
        if release.assets:
            asset_links = []
            for asset in release.assets[:5]:
                size = self._format_size(asset.size)
                asset_links.append(f"[{asset.name}]({asset.download_url}) - {size}")

            if asset_links:
                downloads_text = "\n".join(asset_links)
                if len(release.assets) > 5:
                    downloads_text += f"\n[View all {len(release.assets)} downloads]({release.html_url})"

                embed.add_field(
                    name="Downloads",
                    value=downloads_text,
                    inline=False
                )

        embed.set_footer(text=f"GitHub {release_type} Release")

        logger.debug("Embed created successfully")
        return embed

    def _split_text(self, text: str, max_length: int) -> list:
        """Split text into chunks of max_length"""
        chunks = []
        current_chunk = ""

        for line in text.split('\n'):
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line
            else:
                current_chunk += line + '\n'

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
