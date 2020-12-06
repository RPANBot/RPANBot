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
from discord import AsyncWebhookAdapter, TextChannel, Webhook
from discord.ext.commands import Cog, bot_has_permissions, command, group, guild_only, has_guild_permissions

from asyncio import TimeoutError
from aiohttp import ClientSession

from textwrap import dedent
from typing import Optional, Union

from discord.helpers.generators import RPANEmbed
from discord.helpers.classes import BNSettingsHandler

from utils.helpers import parse_reddit_username, to_lowercase
from utils.validators import is_valid_prefix, is_valid_reddit_username

from utils.database.models.custom_prefixes import CustomPrefixes
from utils.database.models.broadcast_notifications import BNUser, BNSetting


class Management(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.bn_settings_handler = BNSettingsHandler(self.bot)

        self.invalid_prefix_description = dedent("""
            That is an invalid prefix.

            ```md
            # Requirements:
            · the prefix should not contain: `
            · the prefix should not be blank
            · the prefix should be shorter than 10 characters
            ```
        """)

        self.disallowed_usernames = ["rpanbot"]

    # Stream Notifications
    async def validate_current_selection(self, ctx, handle_reply: bool = True) -> Union[BNSetting, bool]:
        """
        Validate that the currently selected setting is valid.
        :return: The current BNSetting or False.
        """
        setting = self.bn_settings_handler.get_current_setting(ctx.guild.id)
        if setting:
            return setting
        else:
            if handle_reply:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Invalid Selection",
                        description=dedent("""
                            **No valid setting is currently selected.**

                            ```md
                            # Either:
                            · There are currently no stream notification settings for this guild.
                            · The last setting that was selected has been deleted.
                            · An invalid setting is currently selected.
                            ```
                        """),
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
            return False

    @group(aliases=["bn", "sn", "broadcastnotifs"])
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    @bot_has_permissions(embed_links=True, manage_webhooks=True)
    async def streamnotifs(self, ctx) -> None:
        """
        Settings for the notifications when specific users go live.
        """
        if ctx.invoked_subcommand is None:
            relevant_prefix = self.bot.get_primary_prefix(ctx.guild)
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications",
                    url=self.bot.core.settings.links.site_base + "/commands",
                    description=dedent("""
                        **Configure notifications for when certain users go live on RPAN.**
                        Either you didn't enter a subcommand or that is an invalid subcommand.

                        Note: You can use our web dashboard to easily configure stream notification settings.

                        Setup Guide: https://www.reddit.com/r/RPANBot/wiki/stream_notifications

                        If you'd like any help setting this up, then feel free to ask in our support server.
                    """).strip(),
                    fields={
                        f"Standard ({relevant_prefix}streamnotifs)": dedent("""
                            ``list``
                            View a list of your stream notification channels.

                            ``setup (CHANNEL) (USERNAME)``
                            Setup/add a new stream notification channel. You can add more names to the channel later.

                            ``select (ID/CHANNEL)``
                            Select which stream notifications channel you want to modify.

                            ``usernames``
                            View the usernames used by the currently selected channel.

                            ``keywords``
                            View the keywords that are required in the username for a notification (for the current selection).

                            ``subreddits``
                            View the current subreddit filters.

                            ``selected``
                            View which channel you currently have selected.
                        """).format(prefix=relevant_prefix),

                        "Usernames": dedent("""
                            ``{prefix}sn user add (REDDIT USERNAME)``
                            Add a Reddit user (who you want to receive notifications for) to your stream notification settings.

                            ``{prefix}sn user remove (REDDIT USERNAME)``
                            Remove a user from the notification settings on the currently selected channel.
                        """).format(prefix=relevant_prefix),

                        "Keywords": dedent("""
                            Keyword requirements are words/phrases that are needed in the title of a broadcast in order for a notification to be sent.
                            If any single added keyword is found in the title, the notification will be sent.

                            ``{prefix}sn keyword add (KEYWORD)``
                            Add a keyword requirement to the currently selected channel.

                            ``{prefix}sn keyword remove (KEYWORD)``
                            Remove a keyword requirement from the currently selected channel.

                            ``{prefix}sn keyword clear``
                            Remove all keyword filters from the current notification setting.
                        """).format(prefix=relevant_prefix),

                        "Subreddit Filters": dedent("""
                            Subreddit filters will only send stream notifications when a stream is in one of the specified subreddits.

                            *If no subreddit filters are setup, then a notification will be sent for a stream in any RPAN subreddit.*

                            ``{prefix}sn subreddit add (KEYWORD)``
                            Add a subreddit filter to the current notification setting.

                            ``{prefix}sn subreddit remove (KEYWORD)``
                            Remove a subreddit filter to the current notification setting.

                            ``{prefix}sn subreddit clear``
                            Clear all subreddit filters from the current notification setting.
                        """).format(prefix=relevant_prefix),

                        "Other": dedent("""
                            ``{prefix}sn settext (TEXT)``
                            Set some text that is sent with the notifications sent to the select channel.

                            ``{prefix}sn remove (ID *Optional*)``
                            Delete the notification settings for a specified/the currently selected channel.
                        """).format(prefix=relevant_prefix),
                    },
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    # Stream Notifications - Listings
    @streamnotifs.group(name="list", aliases=["settings"])
    async def streamnotifs_list(self, ctx) -> None:
        """
        List all of your stream notification settings.
        """
        settings = self.bn_settings_handler.get_settings(ctx.guild.id)
        if not settings:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Settings List",
                    description=dedent("""
                        There are currently no stream notification setup on this guild.

                        [Click here for a broadcast notifications setup guide.](https://www.reddit.com/r/RPANBot/wiki/stream_notifications)
                    """).strip(),
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        fields = {}
        current_selection = self.bn_settings_handler.id_to_local(ctx.guild.id, self.bn_settings_handler.get_current_selection(ctx.guild.id))
        for i, setting in enumerate(settings[:25]):
            fields[f"#{i + 1}" if i != current_selection else f"#{i + 1}\n(Currently Selected)"] = f"<#{setting.channel_id}>"

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Settings List",
                description="This is a list of stream notification settings that can be selected from.",
                fields=fields,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs.group(name="selected", aliases=["info"])
    async def streamnotifs_selected(self, ctx) -> None:
        """
        View information on the currently selected notification setting.
        """
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        local_id = self.bn_settings_handler.id_to_local(ctx.guild.id, setting.channel_id)
        primary_prefix = self.bot.get_primary_prefix(ctx.guild)
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Currently Selected",
                description=dedent(f"""
                    The currently selected setting is:
                    **#{local_id + 1}** | <#{setting.channel_id}>
                """).strip(),

                fields={
                    "Usernames": f"View with:\n``{primary_prefix}sn usernames``",
                    "Keyword Filters": f"View with:\n``{primary_prefix}sn keywords``",
                    "Subreddit Filters": f"View with:\n``{primary_prefix}sn subreddits``",

                    "Custom Text": setting.custom_text if setting.custom_text is not None else f"None | Setup with ``{primary_prefix}sn settext (your text)``",
                },

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    # Stream Notifications - Setting Controls
    @streamnotifs.group(name="setup")
    async def streamnotifs_setup(self, ctx, channel: Union[TextChannel, int], username: Optional[parse_reddit_username] = None) -> None:
        """
        Setup stream notifications for a new channel
        """
        if isinstance(channel, TextChannel):
            channel = channel.id

        # Check that there isn't a setting for this channel already.
        setting = self.bn_settings_handler.get_setting(ctx.guild.id, channel)
        if setting is not None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Setup",
                    description="There is already a stream notification setting for that channel.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Check that the guild hasn't hit the channel limit.
        channel_limit = self.bn_settings_handler.get_channel_limit(ctx.guild.id)
        if self.bn_settings_handler.query_settings(ctx.guild.id).count() >= channel_limit:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Setup",
                    description=f"You have hit the limit of {channel_limit} notification channels on this guild.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Validate the input username (if any).
        if username is not None:
            if not is_valid_reddit_username(username):
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Setup",
                        description="That is an invalid Reddit username.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return
            elif ctx.author.id not in self.bot.core.settings.ids.bot_developers:
                if username in self.disallowed_usernames:
                    await ctx.send(
                        "",
                        embed=RPANEmbed(
                            title="Stream Notifications · Setup",
                            description="That is a disallowed username for stream notifications.",
                            colour=0x8B0000,

                            user=ctx.author,
                            bot=self.bot,
                            message=ctx.message,
                        )
                    )
                    return

        # Validate that the channel is in this guild.
        channel = await self.bot.find_channel(channel)
        if channel.guild.id != ctx.guild.id:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Setup",
                    description="That channel is not in this guild.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Setup the settings for this channel.
        webhook = await channel.create_webhook(
            name="RPANBot Stream Notifications",
            reason="Notifications setup via a command.",
        )

        setting = BNSetting(
            guild_id=ctx.guild.id,
            channel_id=channel.id,
            webhook_url=webhook.url,
        )

        if username is not None:
            user = self.bot.db_session.query(BNUser).filter_by(username=username).first()
            if user is None:
                user = BNUser(username=username)
                self.bot.db_session.add(user)
            setting.users.append(user)

        self.bot.db_session.add(setting)
        self.bot.db_session.commit()

        # Set the current guild selection to the new setting.
        self.bn_settings_handler.selections[ctx.guild.id] = channel.id

        # Send a success message.
        fields = {"Channel": f"<#{channel.id}>"}
        if username is not None:
            fields["User"] = f"``u/{username}``"

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Setup",
                description="Succesfully setup stream notifications on that channel.",
                fields=fields,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs.group(name="select")
    async def streamnotifs_select(self, ctx, channel: Union[TextChannel, int] = 1) -> None:
        """
        Select a stream notifications channel to modify settings for.
        """
        if isinstance(channel, TextChannel):
            channel = channel.id

        setting = self.bn_settings_handler.get_by_either_id(ctx.guild.id, channel)
        if setting is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Setting Selection",
                    description="That is not a valid setting. Do you have stream notifications setup on that channel?",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        self.bn_settings_handler.selections[ctx.guild.id] = setting.channel_id
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Setting Selection",
                description=dedent(f"""
                    Selected the <#{setting.channel_id}> channel.

                    Any specific notification settings you change will be for this channel.
                """).strip(),

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    # Stream Notifications - Usernames
    @streamnotifs.group(name="usernames", aliases=["users", "user", "username"])
    async def streamnotifs_usernames(self, ctx) -> None:
        """
        Lists all the usernames on the currently selected channel.
        """
        if ctx.invoked_subcommand is None:
            # Check if the currently selected setting is valid.
            setting = await self.validate_current_selection(ctx)
            if setting is False:
                return

            usernames_text = "None"
            if setting.users.count():
                usernames_text = ", ".join([f"``{user.username}``" for user in setting.users])

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Users",
                    fields={
                        "List": usernames_text,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @streamnotifs_usernames.group(name="add")
    async def streamnotifs_usernames_add(self, ctx, username: parse_reddit_username) -> None:
        """Add a notifications user to the current channel."""
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        # Check that the username is valid.
        if not is_valid_reddit_username(username):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Users",
                    description="That is not a valid Reddit username.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Disallowed stream notification usernames.
        if ctx.author.id not in self.bot.core.settings.ids.bot_developers:
            if username in self.disallowed_usernames:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Users",
                        description="That is a disallowed username for stream notifications.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

        if setting.users.count() >= 50:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Users",
                    description="This channel is currently at the limit of 50 users.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Check if a BNUser record exists for that username.
        # If there isn't already a record for the user then add one.
        # If there is already a record for the user, then check that they are not already added to this BNSetting.
        user = self.bot.db_session.query(BNUser).filter_by(username=username).first()
        if user is None:
            user = BNUser(username=username)
            self.bot.db_session.add(user)
        else:
            if setting in user.notifications_for:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Users",
                        description=f"That user is already added to the settings for <#{setting.channel_id}>",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

        setting.users.append(user)
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Users",
                description=f"You will now receive notifications for broadcasts from ``u/{user.username}`` in <#{setting.channel_id}>",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs_usernames.group(name="remove", aliases=["delete", "rem"])
    async def streamnotifs_usernames_remove(self, ctx, username: parse_reddit_username) -> None:
        """Stop receiving notifications for a specified user."""
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        # Check that the username is valid.
        if not is_valid_reddit_username(username):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Users",
                    description="That is not a valid Reddit username.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        user = self.bot.db_session.query(BNUser).filter_by(username=username).first()

        is_valid_removal = True
        if user is None:
            is_valid_removal = False
        elif setting not in user.notifications_for:
            is_valid_removal = False

        if not is_valid_removal:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Users",
                    description=f"That user is not in the settings for <#{setting.channel_id}>",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        setting.users.remove(user)
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Users",
                description=f"You will no longer receive notifications for ``u/{user.username}`` in <#{setting.channel_id}>",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs_usernames.group(name="clear", aliases=["wipe"])
    async def streamnotifs_usernames_clear(self, ctx) -> None:
        """Delete all notifications users from the current channel."""
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        # Remove all users.
        setting.users = []
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Users",
                description=f"<#{setting.channel_id}> will no longer receive notifications for any users.",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    # Stream Notifications - Keywords
    @streamnotifs.group(name="keywords", aliases=["keyword"])
    async def streamnotifs_keywords(self, ctx) -> None:
        """
        Lists all the keyword filters on the currently selected channel.
        """
        if ctx.invoked_subcommand is None:
            # Check if the currently selected setting is valid.
            setting = await self.validate_current_selection(ctx)
            if setting is False:
                return

            keyword_filters = setting.keyword_filters
            if not keyword_filters:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Keyword Filters",
                        description=f"There are currently no keyword filters on this notification setting. (<#{setting.channel_id}>)",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

            keyword_filters = list(keyword_filters)

            fields = {}
            for i, keyword in enumerate(keyword_filters):
                fields[f"Filter #{i + 1}"] = keyword

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Keyword Filters",
                    description=f"Here's a list of the current keyword filters for <#{setting.channel_id}>.",
                    fields=fields,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @streamnotifs_keywords.group(name="add")
    async def streamnotifs_keywords_add(self, ctx, *, keyword: to_lowercase) -> None:
        """Add a keyword filter to the current channel."""
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        if setting.keyword_filters is not None:
            if keyword in setting.keyword_filters:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Keyword Filters",
                        description="That keyword filter is already added.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

        # Check that the keyword filters limit hasn't been reached.
        if setting.keyword_filters:
            if len(setting.keyword_filters) >= 25:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Keyword Filters",
                        description="You've reached the limit of 25 keyword filters.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

        # Add the keyword filter.
        keyword_filters = []
        if setting.keyword_filters is not None:
            keyword_filters = list(setting.keyword_filters)
        keyword_filters.append(keyword)

        setting.keyword_filters = keyword_filters
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Keyword Filters",
                description=f"Succesfully added a keyword filter to <#{setting.channel_id}>",
                fields={
                    "Keyword/Phrase": keyword,
                },

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs_keywords.group(name="remove", aliases=["delete", "rem"])
    async def streamnotifs_keywords_remove(self, ctx, *, keyword: to_lowercase) -> None:
        """Remove a keyword filter from the current channel."""
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        if setting.keyword_filters is None or keyword not in setting.keyword_filters:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Keyword Filters",
                    description=f"That keyword was not added in <#{setting.channel_id}>",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Remove the keyword filter.
        keyword_filters = []
        if setting.keyword_filters is not None:
            keyword_filters = list(setting.keyword_filters)
        keyword_filters.remove(keyword)

        setting.keyword_filters = keyword_filters
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Keyword Filters",
                description=f"Succesfully removed a keyword filter from <#{setting.channel_id}>",
                fields={
                    "Keyword/Phrase Removed": keyword,
                },

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs_keywords.group(name="clear", aliases=["wipe"])
    async def streamnotifs_keywords_clear(self, ctx) -> None:
        """Delete all keyword filters from the current channel."""
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        # Remove all keyword filters.
        setting.keyword_filters = []
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Keyword Filters",
                description=f"Removed all keyword filters from <#{setting.channel_id}>",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    # Stream Notifications - Subreddits
    @streamnotifs.group(name="subreddits", aliases=["sub", "subreddit", "subfilter"])
    async def streamnotifs_subreddits(self, ctx) -> None:
        """
        Lists all the subreddit filters on the currently selected channel.
        """
        if ctx.invoked_subcommand is None:
            # Check if the currently selected setting is valid.
            setting = await self.validate_current_selection(ctx)
            if setting is False:
                return

            filters_text = "None"
            subreddit_filters = setting.subreddit_filters
            if subreddit_filters:
                filters_text = "\n".join([f"• ``r/{subreddit}``" for subreddit in subreddit_filters])

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Subreddit Filters",
                    fields={
                        "Subreddit Filters List:": filters_text,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @streamnotifs_subreddits.group(name="add")
    async def streamnotifs_subreddits_add(self, ctx, subreddit: to_lowercase) -> None:
        """Add a subreddit filter to the current channel."""
        # Validate that the subreddit is an RPAN subreddit.
        sub = self.bot.core.rpan_subreddits.ref_to_full(subreddit)
        if sub is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Unknown Subreddit",
                    description=f"'{subreddit}' was not found to be a valid subreddit.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        if setting.subreddit_filters is not None:
            if sub in setting.subreddit_filters:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Subreddit Filters",
                        description=f"``r/{sub}`` is already added as a subreddit filter.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

        # Add the subreddit filter.
        subreddit_filters = []
        if setting.subreddit_filters is not None:
            subreddit_filters = list(setting.subreddit_filters)
        subreddit_filters.append(sub)

        setting.subreddit_filters = subreddit_filters

        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Subreddit Filters",
                description=f"Added ``r/{sub}`` as a subreddit filter for <#{setting.channel_id}>",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs_subreddits.group(name="remove", aliases=["delete", "rem", "rm"])
    async def streamnotifs_subreddits_remove(self, ctx, subreddit: to_lowercase) -> None:
        """Remove a subreddit filter from the current channel."""
        # Validate that the subreddit is an RPAN subreddit.
        sub = self.bot.core.rpan_subreddits.ref_to_full(subreddit)
        if sub is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Unknown Subreddit",
                    description=f"'{subreddit}' was not found to be a valid RPAN subreddit.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        if setting.subreddit_filters is None or sub not in setting.subreddit_filters:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · Subreddit Filters",
                    description=f"'{sub}' was not added as a subreddit filter.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        # Remove the specific subreddit filter.
        subreddit_filters = list(setting.subreddit_filters)
        subreddit_filters.remove(sub)
        setting.subreddit_filters = subreddit_filters
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Subreddit Filters",
                description=f"Removed ``r/{sub}`` from the subreddit filters for <#{setting.channel_id}>",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @streamnotifs_subreddits.group(name="clear", aliases=["wipe"])
    async def streamnotifs_subreddits_clear(self, ctx) -> None:
        """Delete all subreddit filters from the current channel."""
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        # Remove all subreddit filters.
        setting.subreddit_filters = []
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Subreddit Filters",
                description=f"Removed all subreddit filters on <#{setting.channel_id}>",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    # Stream Notifications - Attribute Customisations
    @streamnotifs.group(name="settext")
    async def streamnotifs_settext(self, ctx, *, text: Optional[str] = None) -> None:
        """
        Set some custom text that is sent with notifications on this channel. Remove the custom text by not specifying anything.
        """
        # Check if the currently selected setting is valid.
        setting = await self.validate_current_selection(ctx)
        if setting is False:
            return

        # Check that the custom text is not beyond the limit.
        if text:
            if len(text) > 1000:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Custom Text",
                        description="The input custom text is beyond the 1000 character limit.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

        # Set the custom text.
        setting.custom_text = text
        self.bot.db_session.commit()

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Custom Text",
                description=f"Set some custom text to be sent with notifications on <#{setting.channel_id}>",
                fields={
                    "Custom Text": text,
                },

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    # Stream Notifications - Removing
    @streamnotifs.group(name="remove", aliases=["delete", "del"])
    async def streamnotifs_remove(self, ctx, channel: Optional[Union[TextChannel, int]] = None) -> None:
        """
        Delete a stream notification setting.
        """
        setting = None
        if channel is None:
            # Check if the currently selected setting is valid.
            setting = await self.validate_current_selection(ctx)
            if setting is False:
                return
        else:
            setting = self.bn_settings_handler.get_by_either_id(ctx.guild.id, channel)
            if setting is None:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Stream Notifications · Setting Deletion",
                        description="The channel that you specified is not valid. Is there a stream notification setting on there?",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

        local_id = self.bn_settings_handler.id_to_local(ctx.guild.id, setting.channel_id)
        confirmation_message = await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · Setting Deletion",
                description=dedent(f"""
                    **Are you sure you want to delete the notifications for the following channel?:**
                    Setting #{local_id + 1} - Channel: <#{setting.channel_id}>

                    To confirm, react with the following within the next 30 seconds: ✅
                """).strip(),

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

        def confirmation_check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"

        try:
            await confirmation_message.add_reaction("✅")
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=confirmation_check)
        except TimeoutError:
            await confirmation_message.edit(
                embed=RPANEmbed(
                    title="Stream Notifications · Setting Deletion",
                    description="No confirmation was given within 30 seconds.",

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        else:
            try:
                # Attempt to delete the webhook.
                async with ClientSession() as session:
                    webhook = Webhook.from_url(setting.webhook_url, adapter=AsyncWebhookAdapter(session))
                    await webhook.delete(reason="Deleted via command.")
            except Exception as e:
                print(e)
                pass
            finally:
                # Delete the setting from the database.
                self.bot.db_session.delete(setting)
                self.bot.db_session.commit()

            await confirmation_message.edit(
                embed=RPANEmbed(
                    title="Stream Notifications - Succesful Deletion",
                    description=f"Succesfully deleted Setting #{local_id + 1}: <#{setting.channel_id}>.",
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @streamnotifs.group(name="removeall", aliases=["wipe"])
    @has_guild_permissions(administrator=True)
    async def streamnotifs_removeall(self, ctx) -> None:
        """
        Delete all of your stream notification settings.
        """
        settings = self.bn_settings_handler.query_settings(ctx.guild.id)
        if not settings.count():
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Stream Notifications · All Settings Deletion",
                    description="This guild has no broadcast notification settings.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return
        else:
            settings = settings.all()

        confirmation_message = await ctx.send(
            "",
            embed=RPANEmbed(
                title="Stream Notifications · All Settings Deletion",
                description="Are you sure you want to delete **all** notification settings on this guild?",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

        def confirmation_check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == "✅"

        try:
            await confirmation_message.add_reaction("✅")
            reaction, user = await self.bot.wait_for("reaction_add", timeout=10.0, check=confirmation_check)
        except TimeoutError:
            await confirmation_message.edit(
                embed=RPANEmbed(
                    title="Stream Notifications · All Settings Deletion",
                    description="No confirmation was given within 10 seconds.",

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        else:
            async with ClientSession() as session:
                for setting in settings:
                    try:
                        webhook = Webhook.from_url(setting.webhook_url, adapter=AsyncWebhookAdapter(session))
                        await webhook.delete(reason="Deleting all stream notification settings.")
                    except Exception as e:
                        print(e)
                        pass
                    finally:
                        self.bot.db_session.delete(setting)
            self.bot.db_session.commit()

            await confirmation_message.edit(
                embed=RPANEmbed(
                    title="Stream Notifications · All Settings Deletion",
                    description="Deleted all broadcast notification settings.",

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    # Custom Prefixes
    def format_default_prefixes(self) -> str:
        return ", ".join([f"``{prefix}``" for prefix in self.bot.core.settings.discord.default_prefixes])

    @group(aliases=["customprefix"])
    @guild_only()
    @bot_has_permissions(embed_links=True)
    @has_guild_permissions(manage_guild=True)
    async def prefix(self, ctx) -> None:
        """
        Add/remove custom prefixes for this guild.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes",
                    description=dedent("""
                        No subcommand was input, or that subcommand was not found.

                        **Subcommand List:**
                        ``prefix add (prefix)`` - Add a custom prefix (up to 4).
                        ``prefix remove (prefix)`` - Remove a custom prefix.
                        ``prefix set (prefix)`` - Overrides all other prefixes.
                        ``prefix reset`` - Switch back to using the bot's default prefixes.
                    """).strip(),

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @prefix.group(name="set")
    async def prefix_set(self, ctx, prefix: str) -> None:
        """
        Overide all other custom prefixes and set one.
        """
        prefix = prefix.lower()
        if not is_valid_prefix(prefix):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Invalid Prefix",
                    description=self.invalid_prefix_description,
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            result.prefixes = [prefix]
        else:
            self.bot.db_session.add(
                CustomPrefixes(
                    guild_id=ctx.guild.id,
                    prefixes=[prefix],
                )
            )
        self.bot.db_session.commit()
        del self.bot.prefix_cache[ctx.guild.id]

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Custom Prefixes · Set",
                description=dedent(f"""
                    Succesfully replaced any other custom prefixes and set that one.

                    The bot will now respond to ``{prefix}`` on this guild.

                    ```Example Usage:\n{prefix}help```

                    The bot will still respond to mentions of its name, for example:
                    {self.bot.user.mention} help

                    You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                """).strip(),

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @prefix.group(name="add")
    async def prefix_add(self, ctx, prefix: str) -> None:
        """
        Add a custom prefix to this guild.
        """
        prefix = prefix.lower()
        if not is_valid_prefix(prefix):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Invalid Prefix",
                    description=self.invalid_prefix_description,
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            prefixes = list(result.prefixes)
            if len(prefixes) >= 4:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Prefix Limit",
                        description="This guild has hit the 4 custom prefixes limit.\n\nYou can remove prefixes in order to add more.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

            if any([prefix.startswith(existing_prefix) for existing_prefix in prefixes]):
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Conflict",
                        description="This prefix would conflict with another prefix as this prefix starts with the other prefix.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

            if any([existing_prefix.startswith(prefix) for existing_prefix in prefixes]):
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Conflict",
                        description="Another existing custom prefix starts with this prefix, which would cause a conflict. Remove it to add this as a custom prefix.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

            if prefix not in prefixes:
                prefixes.append(prefix)
                result.prefixes = prefixes
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Add",
                        description=dedent(f"""
                            **Succesfully added a custom prefix.**

                            The bot will now respond to ``{prefix}`` on this guild.

                            ```Example Usage:\n{prefix}help```

                            You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                        """).strip(),

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
            else:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Add",
                        description="That custom prefix is already added on this guild.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return
        else:
            self.bot.db_session.add(
                CustomPrefixes(
                    guild_id=ctx.guild.id,
                    prefixes=[prefix],
                )
            )

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Set",
                    description=dedent(f"""
                        **Succesfully set a new custom prefix.**

                        The bot will now only respond to ``{prefix}`` and mentions on this guild.

                        ```Example Usage:\n{prefix}help```

                        You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                    """).strip(),

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        self.bot.db_session.commit()
        del self.bot.prefix_cache[ctx.guild.id]

    @prefix.group(name="remove", aliases=["rem", "delete"])
    async def prefix_remove(self, ctx, prefix: str) -> None:
        """
        Remove a custom prefix from this guild.
        """
        prefix = prefix.lower()
        if not is_valid_prefix(prefix):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Invalid Prefix",
                    description=self.invalid_prefix_description,
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            prefixes = list(result.prefixes)

            if prefix in prefixes:
                other_info = ""

                if len(prefixes) > 1:
                    prefixes.remove(prefix)
                    result.prefixes = prefixes
                else:
                    other_info = f"\n\nAll custom prefixes have been removed. Defaulting to: {self.format_default_prefixes()}"
                    self.bot.db_session.delete(result)

                self.bot.db_session.commit()
                del self.bot.prefix_cache[ctx.guild.id]

                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Remove",
                        description=dedent(f"""
                            **Succesfully removed the prefix ``{prefix}``.**{other_info}

                            You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                        """).strip(),

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
            else:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Remove",
                        description="That prefix is not a responding prefix on this guild.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return
        else:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Remove",
                    description="There are no custom prefixes set up for this guild.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @prefix.group(name="reset", aliases=["default"])
    async def prefix_reset(self, ctx) -> None:
        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            self.bot.db_session.delete(result)
            self.bot.db_session.commit()
            del self.bot.prefix_cache[ctx.guild.id]

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes",
                    description="Succesfully reset to the default prefixes.",
                    fields={
                        "Default Prefixes": self.format_default_prefixes(),
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        else:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Reset to Default",
                    description="There are no custom prefixes set up for this guild.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )


def setup(bot) -> None:
    bot.add_cog(Management(bot))
