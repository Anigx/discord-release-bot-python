import asyncio
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from src.config import Config, load_config
from src.logger import logger
from src.services import DiscordService, FormatterService, GitHubService
from src.state import StateManager

ReleaseType = Literal['stable', 'beta']


class ReleaseBot(commands.Cog):
    """Discord bot for GitHub release announcements."""

    settings = app_commands.Group(
        name='settings',
        description='Configure the release bot for this server.',
    )

    def __init__(self, bot: commands.Bot, config: Config):
        self.bot = bot
        self.config = config
        self.autopost_task_started = False

    @commands.Cog.listener()
    async def on_ready(self):
        """Start the command sync and release polling loop once."""
        logger.info(f'Bot is online as {self.bot.user}')

        try:
            synced = await self.bot.tree.sync()
            logger.info(f'Synced {len(synced)} command(s)')
        except Exception as error:
            logger.error(f'Failed to sync commands: {error}')

        if not self.autopost_task_started:
            self.autopost_task_started = True
            asyncio.create_task(self._autopost_loop())
            logger.info('Autopost background task started')

    @settings.command(name='repository', description='Set the GitHub repository for this server.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        owner='GitHub owner, for example Anigx',
        repo='GitHub repository, for example Furya-Public',
        app_name='Name shown in release announcements',
    )
    async def settings_repository(
        self,
        interaction: discord.Interaction,
        owner: str,
        repo: str,
        app_name: str,
    ):
        """Save the release source and display name for the current guild."""
        owner = owner.strip()
        repo = repo.strip()
        app_name = app_name.strip()
        if not owner or not repo or not app_name:
            await interaction.response.send_message(
                'Owner, repository and app name must not be empty.', ephemeral=True
            )
            return

        StateManager.set_repository(interaction.guild_id, owner, repo, app_name)
        await interaction.response.send_message(
            f'Repository set to `{owner}/{repo}` for **{app_name}**.', ephemeral=True
        )
        logger.info(f'Repository configured for guild {interaction.guild_id}: {owner}/{repo}')

    @settings.command(name='channel', description='Set the target channel for stable or beta releases.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        release_type='Which release type should be posted to this channel?',
        channel='Target text channel',
    )
    async def settings_channel(
        self,
        interaction: discord.Interaction,
        release_type: ReleaseType,
        channel: discord.TextChannel,
    ):
        """Save a release destination for the current guild."""
        StateManager.set_channel(interaction.guild_id, release_type, channel.id)
        await interaction.response.send_message(
            f'{release_type.title()} releases will be posted to {channel.mention}.', ephemeral=True
        )
        logger.info(f'{release_type} channel configured for guild {interaction.guild_id}: {channel.id}')

    @settings.command(name='show', description='Show the saved release-bot settings for this server.')
    @app_commands.guild_only()
    async def settings_show(self, interaction: discord.Interaction):
        """Display the current guild configuration."""
        settings = StateManager.get_guild_settings(interaction.guild_id)
        repository = settings.get('repository', {})
        channels = settings.get('channels', {})

        embed = discord.Embed(title='Release Bot Settings', color=discord.Color.blurple())
        embed.add_field(
            name='Repository',
            value=(
                f"`{repository['owner']}/{repository['repo']}`"
                if repository.get('owner') and repository.get('repo') else 'Not configured'
            ),
            inline=False,
        )
        embed.add_field(
            name='App Name', value=repository.get('app_name', 'Not configured'), inline=True
        )
        embed.add_field(
            name='Stable Channel',
            value=f"<#{channels['stable']}>" if channels.get('stable') else 'Not configured',
            inline=True,
        )
        embed.add_field(
            name='Beta Channel',
            value=f"<#{channels['beta']}>" if channels.get('beta') else 'Not configured',
            inline=True,
        )
        embed.add_field(
            name='Autopost',
            value='Enabled' if settings.get('autopost_enabled', False) else 'Disabled',
            inline=True,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name='version', description='Post a stable or beta release to its configured channel.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.describe(
        tag='Specific release tag to post; leave empty for the newest release',
        release_type='Release type to fetch when no tag is given',
    )
    async def version_command(
        self,
        interaction: discord.Interaction,
        tag: Optional[str] = None,
        release_type: ReleaseType = 'stable',
    ):
        """Fetch and post a release to the channel determined by its type."""
        await interaction.response.defer(ephemeral=True)
        settings = StateManager.get_guild_settings(interaction.guild_id)
        repository = settings.get('repository', {})
        if not repository.get('owner') or not repository.get('repo') or not repository.get('app_name'):
            await interaction.followup.send(
                'Configure the repository first with `/settings repository`.', ephemeral=True
            )
            return

        github_service = GitHubService(
            repository['owner'], repository['repo'], self.config.github_token
        )
        release = (
            await github_service.get_release_by_tag(tag)
            if tag else await github_service.get_latest_release(release_type == 'beta')
        )
        if not release or release.draft:
            await interaction.followup.send('No published release was found.', ephemeral=True)
            return

        actual_release_type: ReleaseType = 'beta' if release.prerelease else 'stable'
        channel_id = settings.get('channels', {}).get(actual_release_type)
        if not channel_id:
            await interaction.followup.send(
                f'Configure a {actual_release_type} channel with `/settings channel` first.',
                ephemeral=True,
            )
            return

        posted = await self._post_release(repository['app_name'], release, channel_id)
        if not posted:
            await interaction.followup.send('The release could not be posted. Check the bot permissions.', ephemeral=True)
            return

        StateManager.set_last_posted_release_id(interaction.guild_id, actual_release_type, release.id)
        await interaction.followup.send(
            f'**{release.tag_name}** was posted to <#{channel_id}> as a {actual_release_type} release.',
            ephemeral=True,
        )

    @app_commands.command(name='autopost', description='Toggle automatic stable and beta release announcements.')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def autopost_command(self, interaction: discord.Interaction):
        """Toggle automatic posting for the current guild."""
        settings = StateManager.get_guild_settings(interaction.guild_id)
        repository = settings.get('repository', {})
        channels = settings.get('channels', {})
        if not repository.get('owner') or not repository.get('repo'):
            await interaction.response.send_message(
                'Configure the repository first with `/settings repository`.', ephemeral=True
            )
            return
        if not channels.get('stable') or not channels.get('beta'):
            await interaction.response.send_message(
                'Configure both Stable and Beta channels with `/settings channel` first.', ephemeral=True
            )
            return

        enabled = StateManager.toggle_autopost(interaction.guild_id)
        await interaction.response.send_message(
            f'Automatic posting is now **{"enabled" if enabled else "disabled"}**.', ephemeral=True
        )

    async def _post_release(self, app_name: str, release, channel_id: int) -> bool:
        formatter_service = FormatterService(app_name)
        discord_service = DiscordService(self.bot, channel_id)
        return await discord_service.post_release(formatter_service.create_release_embed(release))

    async def _autopost_loop(self):
        """Check each configured guild for new stable and beta releases every minute."""
        await self.bot.wait_until_ready()
        logger.info('Autopost loop is running')

        while True:
            await asyncio.sleep(60)
            try:
                for guild in self.bot.guilds:
                    await self._autopost_guild(guild.id)
            except Exception as error:
                logger.error(f'Autopost loop error: {error}')

    async def _autopost_guild(self, guild_id: int):
        settings = StateManager.get_guild_settings(guild_id)
        if not settings.get('autopost_enabled'):
            return

        repository = settings.get('repository', {})
        channels = settings.get('channels', {})
        if not repository.get('owner') or not repository.get('repo') or not repository.get('app_name'):
            logger.warning(f'Autopost skipped for guild {guild_id}: repository is not configured')
            return

        github_service = GitHubService(repository['owner'], repository['repo'], self.config.github_token)
        releases = await github_service.get_latest_releases()
        for release_type, release in releases.items():
            channel_id = channels.get(release_type)
            if not release or not channel_id:
                continue
            if release.id == StateManager.get_last_posted_release_id(guild_id, release_type):
                continue

            posted = await self._post_release(repository['app_name'], release, channel_id)
            if posted:
                StateManager.set_last_posted_release_id(guild_id, release_type, release.id)
                logger.info(f'Autopost: posted {release.tag_name} to guild {guild_id}')

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Return actionable messages for command permission and guild errors."""
        if isinstance(error, app_commands.MissingPermissions):
            message = 'You need the **Manage Server** permission to use this command.'
        elif isinstance(error, app_commands.NoPrivateMessage):
            message = 'This command can only be used in a server.'
        else:
            logger.error(f'App command error: {error}')
            message = 'The command failed. Check the bot logs for details.'

        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup_bot() -> commands.Bot:
    """Set up and return the Discord bot."""
    intents = discord.Intents.default()
    intents.guilds = True
    bot = commands.Bot(command_prefix='/', intents=intents)
    await bot.add_cog(ReleaseBot(bot, load_config()))
    return bot
