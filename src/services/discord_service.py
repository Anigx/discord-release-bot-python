import discord
from src.logger import logger

class DiscordService:
    """Service for Discord posting operations"""

    def __init__(self, client: discord.Client, announcement_channel_id: str):
        self.client = client
        self.announcement_channel_id = announcement_channel_id

    async def post_release(self, embed: discord.Embed) -> bool:
        """Post release embed to announcement channel"""
        try:
            channel = self.client.get_channel(int(self.announcement_channel_id))

            if not channel:
                channel = await self.client.fetch_channel(int(self.announcement_channel_id))

            if not channel or not isinstance(channel, discord.TextChannel):
                logger.error(f"Channel {self.announcement_channel_id} not found or not a text channel")
                return False

            await channel.send(embed=embed)
            logger.info(f"Release posted to channel {self.announcement_channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to post release: {e}")
            raise

    async def post_confirmation(self, channel: discord.TextChannel, embed: discord.Embed) -> bool:
        """Post confirmation embed to command channel"""
        try:
            await channel.send(embed=embed)
            return True
        except Exception as e:
            logger.error(f"Failed to post confirmation: {e}")
            raise
