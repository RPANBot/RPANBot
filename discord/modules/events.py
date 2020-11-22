"""
Copyright 2020 RPANBot

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from discord import Guild, Member, Message
from discord.ext.commands import (
    Cog,
    BadArgument, BotMissingPermissions, CommandNotFound, CheckFailure, MissingRequiredArgument, MissingPermissions,
    BucketType, CooldownMapping
)

from textwrap import dedent

from datetime import timezone

from utils.helpers import erase_guild_settings
from utils.database.models.exclusions import ExcludedGuild, ExcludedUser

from discord.helpers.generators import RPANEmbed
from discord.helpers.checks import is_not_excluded
from discord.helpers.exceptions import DeveloperCheckFailure, ExcludedUserBlocked, GlobalCooldownFailure


class Events(Cog):
    """
    This cog handles watching Discord events.
    For example: deleting a guild's setting when the bot leaves a guild.
    """
    def __init__(self, bot) -> None:
        self.bot = bot

        self.bot.check(is_not_excluded)
        self.bot.before_invoke(self.before_invoke)

        self.spam_counter = {}
        self.spam_cooldown = CooldownMapping.from_cooldown(rate=10, per=7.5, type=BucketType.user)

        self.exclusion_watch = None

    @Cog.listener()
    async def on_member_join(self, member: Member) -> None:
        self.bot.user_count += 1

    @Cog.listener()
    async def on_member_remove(self, member: Member) -> None:
        self.bot.user_count += 1

    @Cog.listener()
    async def on_message(self, message: Message) -> None:
        """
        Handles checking messages for commands.
        """
        # Ignore the message if it's from a bot.
        if message.author.bot:
            return

        # Reply with the prefixes if the message is the bot's mention.
        bot_mentions = [f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>"]
        if message.content in bot_mentions:
            prefixes = ", ".join([f"``{prefix}``" for prefix in self.bot.get_prefixes(message.guild)])
            await message.channel.send(f"Hello {message.author.mention}! I respond to the following prefixes here:\n{prefixes}")

    async def before_invoke(self, ctx):
        """
        Handles some events before continuing with invoking a command.
        """
        # Handle the global commands cooldown.
        cooldown_bucket = self.spam_cooldown.get_bucket(ctx.message)
        cooldown_retry = cooldown_bucket.update_rate_limit(ctx.message.created_at.replace(tzinfo=timezone.utc).timestamp())
        if cooldown_retry:
            # Increment the user's spam counter.
            if ctx.author.id in self.spam_counter:
                self.spam_counter[ctx.author.id] += 1
            else:
                self.spam_counter[ctx.author.id] = 1

            # Load the spam log channel.
            log_channel = await self.bot.find_channel(self.bot.core.settings.ids.exclusions_and_spam_channel)

            # Check if the user has been continually spamming.
            if self.spam_counter[ctx.author.id] >= 5:
                self.bot.db_session.add(ExcludedUser(user_id=ctx.author.id))
                self.bot.db_session.commit()
                del self.bot.excluded_user_cache[ctx.author.id]
                del self.spam_counter[ctx.author.id]

                await log_channel.send(
                    "",
                    embed=RPANEmbed(
                        title="Auto Ban Issued",
                        description="A user has been banned due to the amount of cooldowns they've received.",
                        colour=0x800000,

                        fields={
                            "User": f"{ctx.author} ({ctx.author.id})",
                            "Guild": f"{ctx.guild.name} ({ctx.guild.id})",
                            "Guild Owner": f"{ctx.guild.owner}\n({ctx.guild.owner_id})",
                        },
                    ),
                )
            else:
                await log_channel.send(
                    "",
                    embed=RPANEmbed(
                        title="Spam Note",
                        description="A user has been marked as spamming.",
                        colour=0xFFFF00,

                        fields={
                            "User": f"{ctx.author} ({ctx.author.id})",
                            "Guild": f"{ctx.guild.name} ({ctx.guild.id})",
                            "Guild Owner": f"{ctx.guild.owner}\n({ctx.guild.owner_id})",
                        },
                    ),
                )

            # Raise the exception that the user is on cooldown.
            raise GlobalCooldownFailure
        else:
            if ctx.author.id in self.spam_counter:
                self.spam_counter[ctx.author.id]

        # Start typing before executing the command.
        await ctx.trigger_typing()

    @Cog.listener()
    async def on_guild_join(self, guild) -> None:
        # Check that the guild isn't banned from the bot.
        is_banned = self.bot.db_session.query(ExcludedGuild).filter_by(guild_id=guild.id).first()
        if is_banned:
            self.exclusion_watch = guild.id
            log_channel = await self.bot.find_channel(self.bot.core.settings.ids.exclusions_and_spam_channel)
            await log_channel.send(
                "",
                embed=RPANEmbed(
                    title="Excluded Guild Join Attempt",
                    description="A banned guild attempted to add the bot.",
                    fields={
                        "Guild Name": guild.name,
                        "Guild ID": guild.id,
                        "Owner": f"{guild.owner}\n({guild.owner_id})",
                    },

                    thumbnail=guild.icon_url,
                ),
            )

            await guild.leave()
            return

        # Check that the guild owner isn't banned from the bot.
        owner_is_banned = self.bot.db_session.query(ExcludedUser).filter_by(user_id=guild.owner_id).first()
        if owner_is_banned:
            self.exclusion_watch = guild.id
            log_channel = await self.bot.find_channel(self.bot.core.settings.ids.exclusions_and_spam_channel)
            await log_channel.send(
                "",
                embed=RPANEmbed(
                    title="Excluded User Bot Invite",
                    description="A banned bot user attempted to add the bot to their guild.",
                    fields={
                        "Guild Name": guild.name,
                        "Guild ID": guild.id,
                        "Owner": f"{guild.owner}\n({guild.owner_id})",
                    },

                    thumbnail=guild.icon_url,
                ),
            )

            await guild.leave()
            return

        # Log that the bot has joined a new guild.
        log_channel = await self.bot.find_channel(self.bot.core.settings.ids.join_leave_channel)
        await log_channel.send(
            "",
            embed=RPANEmbed(
                title="Guild Joined",
                description=f"Now in {len(self.bot.guilds)} guilds.",
                colour=0x32CD32,

                fields={
                    "Guild Name": guild.name,
                    "Guild ID": guild.id,
                    "Owner": f"{guild.owner}\n({guild.owner_id})",
                    "Member Count": guild.member_count,
                },

                thumbnail=guild.icon_url,
            ),
        )

    @Cog.listener()
    async def on_guild_remove(self, guild: Guild):
        # Ignore sending a message if the guild was left because it's banned.
        if guild.id == self.exclusion_watch:
            return

        # Delete any stored settings that the bot had for the guild.
        erase_guild_settings(self.bot.db_session, guild.id)
        if guild.id in self.bot.prefix_cache:
            del self.bot.prefix_cache[guild.id]

        # Log that the bot has left a guild.
        log_channel = await self.bot.find_channel(self.bot.core.settings.ids.join_leave_channel)
        await log_channel.send(
            "",
            embed=RPANEmbed(
                title="Guild Left",
                description=f"Now in {len(self.bot.guilds)} guilds.",
                colour=0x8B0000,

                fields={
                    "Guild Name": guild.name,
                    "Guild ID": guild.id,
                    "Owner": f"{guild.owner}\n({guild.owner_id})",
                    "Member Count": guild.member_count,
                },

                thumbnail=guild.icon_url,
            ),
        )

    @Cog.listener()
    async def on_command_error(self, ctx, error: Exception) -> None:
        # Ignore if the exception is command not found.
        if isinstance(error, CommandNotFound):
            return

        # Log the exception if it isn't in the exclusion list.
        print(error)
        if self.bot.core.sentry:
            exclusion_list = [BadArgument, BotMissingPermissions, CheckFailure, ExcludedUserBlocked, MissingPermissions, MissingRequiredArgument, GlobalCooldownFailure]
            if not any([isinstance(error, excluded_error) for excluded_error in exclusion_list]):
                self.bot.core.sentry.capture_exception(error)

        # Return if there is already an error handler for this command.
        cmd = ctx.command
        if hasattr(cmd, "on_error"):
            return

        # Don't send error messages for some exceptions.
        if isinstance(error, ExcludedUserBlocked) or isinstance(error, GlobalCooldownFailure):
            return

        # Send an error message to other exceptions.
        if isinstance(error, BotMissingPermissions):
            missing_perms = ", ".join(error.missing_perms)
            if "embed_links" not in missing_perms:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Missing Permissions",
                        description=f"The bot is missing the following permissions that are required for this command:\n{missing_perms}",
                        colour=0x8B0000,
                    ),
                )
            else:
                await ctx.send(
                    dedent(f"""
                        **Missing Permissions**
                        The bot is missing the following permissions that are required for this command (some required for core functionality):
                        ``{missing_perms}``
                    """),
                )
        elif isinstance(error, MissingPermissions):
            missing_perms = ", ".join(error.missing_perms)
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Insufficient Permissions",
                    description=f"You require the following guild permission(s) to use this command: ``{missing_perms}``",
                    colour=0x8B0000,
                ),
            )
        elif isinstance(error, DeveloperCheckFailure):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Insufficient Permissions",
                    description="This command can only be accessed by the bot's core developers.",
                    colour=0x8B0000,
                ),
            )
        elif isinstance(error, CheckFailure):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Insufficient Permissions",
                    description="This command cannot run here.",
                    colour=0x8B0000,
                ),
            )
        elif isinstance(error, BadArgument):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="You've input something wrong.",
                    description=f"The following argument was input incorrectly: '{error.param}'",
                    colour=0x8B0000,
                ),
            )
        elif isinstance(error, MissingRequiredArgument):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Missing Argument",
                    description=dedent(f"""
                        A required argument for this command is missing.

                        **Usage:**
                        ``{cmd.name} {cmd.signature}``

                        **Missing Argument:**
                        {error.param.name}

                        **Argument Key**
                        ``[argument]`` optional argument
                        ``<argument>`` required argument
                    """.strip()),
                    colour=0x8B0000,

                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Something went wrong.",
                    description="But don't worry! A report has been sent to the bot's developers.",
                    colour=0x8B0000,

                    fields={
                        "Support Guild": f"[Click here to join the bot support guild.]({self.bot.core.settings.links.support_guild})",
                    },

                    bot=self.bot,
                    message=ctx.message,
                ),
            )

def setup(bot) -> None:
    bot.add_cog(Events(bot))
