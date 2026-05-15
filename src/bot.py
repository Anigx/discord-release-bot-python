import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import asyncio

from src.config import load_config, Config
from src.services import GitHubService, FormatterService, DiscordService
from src.state import StateManager
from src.logger import logger

class ReleaseBot(commands.Cog):
    """Discord bot for GitHub release announcements"""

    def __init__(self, bot: commands.Bot, config: Config):
        self.bot = bot
        self.config = config
        self.autopost_task_started = False

    @commands.Cog.listener()
    async def on_ready(self):
        """Bot is ready"""
        logger.info(f"✅ Bot is online as {self.bot.user}")
        logger.info(f"📢 Announcement Channel ID: {self.config.bot_announcement_channel_id}")
        logger.info(f"🔗 GitHub: {self.config.github_owner}/{self.config.github_repo}")

        # List all guilds
        guilds = self.bot.guilds
        if guilds:
            logger.info(f"[READY] Bot is in {len(guilds)} guild(s):")
            for guild in guilds:
                logger.info(f"[READY]   - {guild.name} (ID: {guild.id})")
        else:
            logger.warning("[READY] Bot is not in any guilds!")

        # Sync commands
        try:
            synced = await self.bot.tree.sync()
            logger.info(f"✅ Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

        # Start autopost background task
        if not self.autopost_task_started:
            self.autopost_task_started = True
            asyncio.create_task(self._autopost_loop())
            logger.info("✅ Autopost background task started")

    @app_commands.command(name="version", description="Fetch and post app release to announcements")
    @app_commands.describe(
        tag="Specific version/tag to post (e.g., v1.0.0, or leave empty for latest)",
        pre_releases="Include pre-releases (beta, alpha)?"
    )
    async def version_command(
        self,
        interaction: discord.Interaction,
        tag: Optional[str] = None,
        pre_releases: Optional[bool] = None
    ):
        """Handle /version command"""
        try:
            logger.info("Version command handler invoked")

            # Defer reply
            await interaction.response.defer(ephemeral=True)
            logger.info("Command deferred")

            # Get options
            include_pre_releases = pre_releases if pre_releases is not None else self.config.include_pre_releases
            logger.info(
                f"Version command triggered by {interaction.user} - "
                f"tag: {tag or 'latest'}, pre_releases: {include_pre_releases}"
            )

            # Initialize services
            logger.info("Initializing services...")
            github_service = GitHubService(
                self.config.github_owner,
                self.config.github_repo,
                self.config.github_token or None
            )
            formatter_service = FormatterService(self.config.app_name)
            discord_service = DiscordService(
                self.bot,
                self.config.bot_announcement_channel_id
            )
            logger.info("Services initialized")

            # Fetch release
            release = None
            if tag:
                logger.info(f"Fetching specific release with tag: {tag}...")
                release = await github_service.get_release_by_tag(tag)
            else:
                logger.info(f"Fetching latest release from {self.config.github_owner}/{self.config.github_repo}...")
                release = await github_service.get_latest_release(include_pre_releases)

            logger.info(f"Release fetch completed, result: {release.tag_name if release else 'null'}")

            # Check if release found
            if not release:
                error_message = f"Release tag '{tag}' not found" if tag else \
                    ("No releases found (including pre-releases)" if include_pre_releases else "No stable releases found")

                await interaction.followup.send(f"❌ {error_message}", ephemeral=True)
                return

            # Create embed and post
            logger.info("Creating release embed...")
            embed = formatter_service.create_release_embed(release)
            logger.info("Embed created successfully")

            logger.info("Posting release to announcement channel...")
            await discord_service.post_release(embed)
            logger.info("Release posted successfully")

            # Send confirmation
            confirmation_embed = discord.Embed(
                title="Release Posted",
                description=f"**{release.tag_name}** has been posted to <#{self.config.bot_announcement_channel_id}>",
                color=discord.Color.from_rgb(123, 44, 191)
            )

            await interaction.followup.send(embed=confirmation_embed, ephemeral=True)
            logger.info(f"Release {release.tag_name} successfully posted")

        except Exception as e:
            logger.error(f"Error handling version command: {e}")

            error_embed = discord.Embed(
                title="Error",
                description="Failed to fetch and post release. Check bot logs for details.",
                color=discord.Color.red()
            )

            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}")

    @app_commands.command(name="autopost", description="Toggle automatic release posting")
    async def autopost_command(self, interaction: discord.Interaction):
        """Handle /autopost command"""
        try:
            await interaction.response.defer(ephemeral=True)

            new_state = StateManager.toggle_autopost()
            status = "🟢 Enabled" if new_state else "🔴 Disabled"

            embed = discord.Embed(
                title="Autopost Status",
                description=f"Automatic release posting is now **{status.split()[1]}**",
                color=discord.Color.green() if new_state else discord.Color.red()
            )
            embed.add_field(name="Status", value=status, inline=False)
            embed.add_field(
                name="Poll Interval",
                value="Checks every 60 seconds",
                inline=False
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"Autopost toggled to {new_state} by {interaction.user}")

        except Exception as e:
            logger.error(f"Error handling autopost command: {e}")
            error_embed = discord.Embed(
                title="Error",
                description="Failed to toggle autopost setting",
                color=discord.Color.red()
            )
            try:
                await interaction.followup.send(embed=error_embed, ephemeral=True)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}")

    async def _autopost_loop(self):
        """Background loop that checks for new releases every 60 seconds"""
        await self.bot.wait_until_ready()
        logger.info("Autopost loop is running")

        while True:
            try:
                await asyncio.sleep(60)

                # Skip if disabled
                if not StateManager.get_autopost_enabled():
                    continue

                logger.debug("Autopost: Checking for new releases...")

                # Initialize services
                github_service = GitHubService(
                    self.config.github_owner,
                    self.config.github_repo,
                    self.config.github_token or None
                )
                formatter_service = FormatterService(self.config.app_name)
                discord_service = DiscordService(
                    self.bot,
                    self.config.bot_announcement_channel_id
                )

                # Get latest release
                release = await github_service.get_latest_release(self.config.include_pre_releases)

                if not release:
                    logger.debug("Autopost: No releases found")
                    continue

                # Check if already posted
                last_posted_id = StateManager.get_last_posted_release_id()
                if release.id == last_posted_id:
                    logger.debug(f"Autopost: Release {release.tag_name} already posted")
                    continue

                # Post new release
                logger.info(f"Autopost: New release detected - {release.tag_name}")
                embed = formatter_service.create_release_embed(release)
                await discord_service.post_release(embed)

                # Save release ID
                StateManager.set_last_posted_release_id(release.id)
                logger.info(f"Autopost: Successfully posted {release.tag_name}")

            except Exception as e:
                logger.error(f"Autopost loop error: {e}")
                # Continue the loop even if there's an error
                continue


async def setup_bot() -> commands.Bot:
    """Setup and return bot instance"""
    intents = discord.Intents.default()
    intents.guilds = True

    bot = commands.Bot(command_prefix="/", intents=intents)

    # Load config
    config = load_config()

    # Add cog
    await bot.add_cog(ReleaseBot(bot, config))

    return bot
