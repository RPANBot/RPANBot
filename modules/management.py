# Server Management Module
import discord
from discord.ext import commands

from asyncio import sleep, TimeoutError
from aiohttp import ClientSession
from textwrap import dedent

from typing import Optional, Union

from utils.errors import GuildNotifsLimitExceeded
from utils.helpers import generate_embed
from utils.database import BNSetting
from utils.classes import BroadcastNotifSettingsHandler, BNUsernamesAttr, BNKeywordsAttr

def parse_id(string: str) -> Union[int, None]:
    """
    Parses a string to turn a mention (if there's one) into an id.
    :return: The filtered id.
    """
    try:
        return int("".join([char for char in string if char.isdigit()]))
    except ValueError:
        return None

def parse_username(username: str) -> str:
    return username.replace("/u/", "").replace("u/", "").lower()

def parse_keyword(keyword: str) -> str:
    return keyword.lower()

class Management(commands.Cog, name="Server Management"):
    def __init__(self, bot):
        self.bot = bot

        self.invalid_selection_embed = generate_embed(
            title="Stream Notifications - Error",
            description="**No valid selection was found.**\nThere was either:\n* No notification settings setup.\n* An invalid notification setting selection.",
            color=discord.Color(0x8B0000),
        )

        self.notifs_handler = BroadcastNotifSettingsHandler()

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def setprefix(self, ctx, *, prefix):
        """
        Set the bot prefix for the server
        """
        if prefix > 25:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error",
                    description="The custom prefix cannot be longer than 25 characters.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            return

        old_prefix = self.bot.get_relevant_prefix(ctx.message)
        self.bot.set_server_prefix(server=ctx.guild, prefix=prefix)

        await ctx.send(
            "",
            embed=generate_embed(
                title="Prefix Changed",
                fields={
                    "Old Prefix": old_prefix,
                    "New Prefix": prefix,
                },
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot, message=ctx.message,
            )
        )

    @commands.group(aliases=["sn", "bn", "broadcastnotifs", "streamnotifications", "broadcastnotifications"])
    @commands.has_guild_permissions(manage_guild=True)
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def streamnotifs(self, ctx):
        """
        Settings for the notifications when people go live.
        """
        if ctx.invoked_subcommand == None:
            relevant_prefix = self.bot.get_relevant_prefix(ctx.message)
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications",
                    description=dedent("""
                        Configure notifications for when certain users go live on RPAN.
                        Either you didn't enter a subcommand or that is an invalid subcommand.

                        **If you'd like any help setting this up, then feel free to ask in our support server.**

                        Recently we changed the way stream notifications worked (making it more efficient, and allowing it on multiple channels) meaning that you may need to set it up again (if you had it before). We apologise for this inconvenience.
                    """).strip(),
                    fields={
                        f"Standard ({relevant_prefix}streamnotifs)": dedent("""
                            ``list`` - View a list of your stream notification channels.

                            ``setup (CHANNEL) (USERNAME)`` - Setup/add a new stream notification channel. You can add more names to the channel later.

                            ``usernames`` - View the usernames used by the currently selected channel.
                            ``keywords`` - View the keywords that are required in the username for a notification (for the current selection).

                            ``select (ID/CHANNEL)`` - Select which stream notifications channel you want to modifying.
                            ``selected`` - View which channel you currently have selected.
                        """).format(prefix=relevant_prefix),

                        f"Usernames": dedent("""
                            ``{prefix}sn user add (USERNAME)`` - Add a user (who you want to receive notifs for) to your stream notification settings.

                            ``{prefix}sn user remove (USERNAME)`` - Remove a user from the notification settings on the currently selected channel.
                        """).format(prefix=relevant_prefix),

                        f"Keywords": dedent("""
                            Keyword requirements are words/phrases that are needed in the title of a broadcast in order for a notification to be sent.

                            If any single added keyword is found in the title, the notification will be sent.

                            ``{prefix}sn keyword add (KEYWORD)`` - Add a keyword requirement to the currently selected channel.

                            ``{prefix}sn keyword remove (KEYWORD)`` - Remove a keyword requirement from the currently selected channel.
                        """).format(prefix=relevant_prefix),

                        f"Other": dedent("""
                            ``{prefix}sn settext (TEXT)`` - Set some text that is sent with the notifications sent to the select channel.

                            ``{prefix}sn remove (ID *Optional*)`` - Delete the notification settings for a specified/the currently selected channel.
                        """).format(prefix=relevant_prefix),
                    },
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs.group(name="select", help="Select a certain channel to modify the settings for.")
    async def streamnotifs_select(self, ctx, id: parse_id = None):
        if id == None:
            id = 1

        notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, id)
        if notif_setting != None:
            self.notifs_handler.selections[ctx.guild.id] = notif_setting.channel_id
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Settings",
                    description=f"Selected the <#{notif_setting.channel_id}> channel.\nThis means that any stream notif settings you change will affect this channel's settings.\n**Important:** Please note that this selection is guild wide, so if someone else changes it, then it'll change for you as well.",
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="That is not a valid selection.\nPlease use the channel id or the id show in your notif settings list.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs.group(name="selected", aliases=["selection", "setting", "info"], help="View the settings for the current selection.")
    async def streamnotifs_selected(self, ctx):
        current_selection = self.notifs_handler.current_selection(ctx.guild.id)
        notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)
        if notif_setting == None:
            await ctx.send("", embed=self.invalid_selection_embed)
            return

        prefix = self.bot.get_relevant_prefix(ctx.message)
        usernames = BNUsernamesAttr(notif_setting.usernames).items
        notifications_for = ""
        if len(usernames) >= 1:
            shown_limit = 50
            notifications_for = ", ".join([f"``{username}``" for username in usernames[:shown_limit]])
            if len(usernames) > shown_limit:
                notifications_for += "...\n**View more by doing {prefix}sn usernames".format(prefix=prefix)
        else:
            notifications_for = "Currently Nobody"

        selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
        await ctx.send(
            "",
            embed=generate_embed(
                title=f"Stream Notifications - Current Selection #{selection_local_id + 1}",
                fields={
                    "Notifications for": notifications_for,
                    "Channel": f"<#{notif_setting.channel_id}>",
                    "Custom Notifications Text": notif_setting.custom_text if notif_setting.custom_text != None else "None",
                    "Keyword Requirements": f"View using: ``{prefix}sn keywords``",
                },
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @streamnotifs.group(name="setup", help="Setup stream notifications in a certain channel.")
    async def streamnotifs_setup(self, ctx, channel: parse_id, username: Optional[str] = None):
        # Query for notification settings for that channel.
        # If there are already notifications setup for that channel, then send the user a message.
        notif_setting = self.notifs_handler.get_notif_setting(ctx.guild.id, channel)
        if notif_setting != None:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There are already stream notifications setup for that channel.\nYou can select that channel and change settings for it.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            return

        # Ensure that the guild isn't at the stream notifications limit.
        notif_settings_count = self.notifs_handler.get_notif_settings_count(ctx.guild.id)
        notif_settings_limit = self.notifs_handler.current_limit(ctx.guild.id)
        if (notif_settings_count + 1) > notif_settings_limit:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description=f"You have reached the maximum amount ({notif_settings_limit}) of stream notification channels that the guild can have.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            return

        # There are no notification settings for that channel.
        # Attempt to fetch the channel, and setup a webhook.
        webhook = None
        try:
            fetched_channel = await self.bot.fetch_channel(channel)
            if fetched_channel.guild.id == ctx.guild.id:
                webhook = await fetched_channel.create_webhook(name="RPANBot Stream Notifications", reason="Added stream notifs to a channel.")
            else:
                raise
        except Exception as e:
            print(e)
            self.bot.sentry.capture_exception(e)
            webhook = None
            pass

        # Send a message to the user if setting up the webhook didn't work.
        if webhook == None:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="That was an invalid channel/the bot was unable to setup a webhook there.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            return

        # Add the new setting.
        notif_setting = BNSetting(
            guild_id=ctx.guild.id,
            channel_id=channel,
            webhook_url=webhook.url,
            usernames=f"[\"{username}\"]" if username != None else "[]",
        )
        self.bot.db_session.add(notif_setting)
        self.bot.db_session.commit()

        # Send a message to the user.
        fields = {}
        if username:
            fields["Username"] = username
        fields["Channel"] = f"<#{channel}>"

        await ctx.send(
            "",
            embed=generate_embed(
                title="Stream Notifications",
                description="Succesfully setup stream notifications for that channel.",
                fields=fields,
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @streamnotifs.group(name="list", aliases=["settings"], help="Shows a list of stream notification settings that can be selected from.")
    async def streamnotifs_list(self, ctx):
        # TODO (low priority): Add the ability for a paginated list (to allow for more than 25 stream notification settings to be listed).
        notif_settings = self.notifs_handler.get_notif_settings(ctx.guild.id)
        if notif_settings != None:
            fields = {}
            current_selection = self.notifs_handler.parse_id_to_local(ctx.guild.id, self.notifs_handler.current_selection(ctx.guild.id))
            for i, setting in enumerate(notif_settings[:25]):
                fields[f"Setting {i + 1}" if i != current_selection else f"Setting {i + 1}\n(Currently Selected)"] = f"<#{setting.channel_id}>"

            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - List",
                    description=f"This is a list of stream notification settings that can be selected from.",
                    fields=fields,
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There are currently no stream notification setup on this guild.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs.group(name="usernames", aliases=["username", "user", "users"], help="View/add to/modify the usernames used by the currently selected channel.")
    async def streamnotifs_usernames(self, ctx):
        # If an invalid subcommand was provided, then show the usernames list.
        if ctx.invoked_subcommand == None:
            notif_setting, current_selection = None, None
            possible_id = parse_id(ctx.subcommand_passed) if ctx.subcommand_passed != None else None
            if possible_id != None:
                notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, possible_id)
                current_selection = notif_setting.channel_id
            else:
                current_selection = self.notifs_handler.current_selection(ctx.guild.id)
                notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

            if notif_setting == None:
                await ctx.send("", embed=self.invalid_selection_embed)
                return

            fields = {}
            usernames = BNUsernamesAttr(notif_setting.usernames).items
            if len(usernames) >= 1:
                # Split the usernames (should there be more than 45) so they can be split among different embed fields.
                split_usernames = [usernames[i:i + 45] for i in range(0, len(usernames), 45)][:25]
                for i, usernames_set in enumerate(split_usernames):
                    fields[f"Usernames (Section #{i + 1})"] = ", ".join([f"``{username}``" for username in usernames_set])
            else:
                fields["Usernames"] = "None"

            selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
            await ctx.send(
                "",
                embed=generate_embed(
                    title=f"Stream Notifications - Usernames for Setting #{selection_local_id + 1}",
                    description=f"Channel: <#{notif_setting.channel_id}>",
                    fields=fields,
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs_usernames.group(name="add", help="Add a user who you want to get notifications from (when they go live).")
    async def streamnotifs_usernames_add(self, ctx, username: parse_username = None):
        current_selection = self.notifs_handler.current_selection(ctx.guild.id)
        notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

        if notif_setting == None:
            await ctx.send("", embed=self.invalid_selection_embed)
            return

        if username in ["", None] or len(username) > 22:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error",
                    description="You've not input a username/the username was too long (above 22 characters).",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        usernames = BNUsernamesAttr(notif_setting.usernames)
        # Make sure that the channel hasn't hit the username maximum.
        if len(usernames.items) >= 1125:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error",
                    description="You are currently at the stream notifications maximum number of users (1125).",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        username_added = usernames.add(username)
        if username_added:
            notif_setting.usernames = str(usernames)
            self.bot.db_session.commit()

            selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
            await ctx.send(
                "",
                embed=generate_embed(
                    title=f"Stream Notifications - Added u/{username}",
                    description=f"**Succesfully added that user to your notifications for the following channel:**\nSetting #{selection_local_id + 1} - Channel: <#{notif_setting.channel_id}>",
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title=f"Stream Notifications - u/{username}",
                    description=f"**That user is already in your stream notifs for:** <#{notif_setting.channel_id}>",
                    footer_text=f"Requested by {ctx.author}",
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs_usernames.group(name="remove", help="Remove a user from the stream notifs (for the currently selected channel).")
    async def streamnotifs_usernames_remove(self, ctx, username: parse_username = None):
        current_selection = self.notifs_handler.current_selection(ctx.guild.id)
        notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

        if notif_setting == None:
            await ctx.send("", embed=self.invalid_selection_embed)
            return

        if username in ["", None] or len(username) > 22:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error",
                    description="You've not input a username OR the username was too long to be in a notification setting (above 22 characters).",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        usernames = BNUsernamesAttr(notif_setting.usernames)
        username_removed = usernames.remove(username)
        if username_removed:
            notif_setting.usernames = str(usernames)
            self.bot.db_session.commit()

            selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
            await ctx.send(
                "",
                embed=generate_embed(
                    title=f"Stream Notifications - Removed u/{username}",
                    description=f"**Succesfully removed that user from your notifications for the following channel:**\nSetting #{selection_local_id + 1} - Channel: <#{notif_setting.channel_id}>",
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title=f"Stream Notifications - u/{username}",
                    description=f"**That user is not in your stream notifications for:** <#{notif_setting.channel_id}>",
                    footer_text=f"Requested by {ctx.author}",
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs.group(name="keywords", aliases=["keyword", "kw"], help="View the keyword filters used by the currently selected channel.")
    async def streamnotifs_keywords(self, ctx):
        # If an invalid subcommand was provided then show the keyword list.
        if ctx.invoked_subcommand == None:
            notif_setting, current_selection = None, None
            possible_id = parse_id(ctx.subcommand_passed) if ctx.subcommand_passed != None else None
            if possible_id != None:
                notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, possible_id)
                current_selection = notif_setting.channel_id
            else:
                current_selection = self.notifs_handler.current_selection(ctx.guild.id)
                notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

            if notif_setting == None:
                await ctx.send("", embed=self.invalid_selection_embed)
                return

            fields = {}
            keywords = BNKeywordsAttr(notif_setting.keywords).items
            if len(keywords) >= 1:
                for i, keyword in enumerate(keywords[:25]):
                    fields[f"Keyword #{i + 1}"] = f"``{keyword}``"
            else:
                fields["Keywords"] = "None"

            selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
            await ctx.send(
                "",
                embed=generate_embed(
                    title=f"Stream Notifications - Keyword Filters for Setting #{selection_local_id + 1}",
                    description=f"Channel: <#{notif_setting.channel_id}>\n**A keyword is a word/phrase that is required in the title of a broadcast for a notification to be sent.**",
                    fields=fields,
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs_keywords.group(name="add", help="Add a keyword filter.")
    async def streamnotifs_keywords_add(self, ctx, *, keyword: parse_keyword):
        current_selection = self.notifs_handler.current_selection(ctx.guild.id)
        notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

        if notif_setting == None:
            await ctx.send("", embed=self.invalid_selection_embed)
            return

        if len(keyword) > 1024:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error",
                    description="That keyword is too long (it has to be below 1024 characters).",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        keywords = BNKeywordsAttr(notif_setting.keywords)
        # Make sure that the channel hasn't hit the keywords maximum.
        if len(keywords.items) >= 25:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error",
                    description="You are currently at the keywords maximum (25).",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        keyword_added = keywords.add(keyword)
        if keyword_added:
            notif_setting.keywords = str(keywords)
            self.bot.db_session.commit()

            selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Added Keyword",
                    description=f"Succesfully added that as one of the possible keyword requirements for the following channel:\nSetting #{selection_local_id + 1} - Channel: <#{notif_setting.channel_id}>",
                    fields={
                        "Added Keyword": keyword,
                    },
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Keyword Failure",
                    description=f"That keyword is already added for: <#{notif_setting.channel_id}>",
                    footer_text=f"Requested by {ctx.author}",
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs_keywords.group(name="remove", help="Remove a keyword filter.")
    async def streamnotifs_keywords_remove(self, ctx, *, keyword: parse_keyword):
        current_selection = self.notifs_handler.current_selection(ctx.guild.id)
        notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

        if notif_setting == None:
            await ctx.send("", embed=self.invalid_selection_embed)
            return

        keywords = BNKeywordsAttr(notif_setting.keywords)
        keyword_removed = keywords.remove(keyword)
        if keyword_removed:
            notif_setting.usernames = str(keywords)
            self.bot.db_session.commit()

            selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
            await ctx.send(
                "",
                embed=generate_embed(
                    title=f"Stream Notifications - Removed u/{username}",
                    description=f"Succesfully removed that user from your keywords list for the following channel:\nSetting #{selection_local_id + 1} - Channel: <#{notif_setting.channel_id}>",
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Keyword Failure",
                    description=f"That keyword was not added on: <#{notif_setting.channel_id}>",
                    footer_text=f"Requested by {ctx.author}",
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @streamnotifs.group(name="settext", aliases=["text"], help="Set some text that is sent with the notification when you go live.")
    async def streamnotifs_settext(self, ctx, *, custom_text):
        current_selection = self.notifs_handler.current_selection(ctx.guild.id)
        notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

        if notif_setting == None:
            await ctx.send("", embed=self.invalid_selection_embed)
            return

        if len(custom_text) > 1024:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error",
                    description="That custom text is above the limit (1024 characters).",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        notif_setting.custom_text = custom_text
        self.bot.db_session.commit()

        selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
        await ctx.send(
            "",
            embed=generate_embed(
                title="Stream Notifications - Set Custom Text",
                description=f"**Succesfully changed the custom text for the following channel:**\nSetting #{selection_local_id + 1} - Channel: <#{notif_setting.channel_id}>",
                fields={
                    "New Text": custom_text,
                },
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @streamnotifs.group(name="remove", aliases=["delete"], help="Delete the currently selected/a specified stream notification setting.")
    async def streamnotifs_remove(self, ctx, id: parse_id = None):
        notif_setting, current_selection = None, None
        id = parse_id(ctx.subcommand_passed) if ctx.subcommand_passed != None else None
        if id != None:
            notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, id)
            current_selection = notif_setting.channel_id
        else:
            current_selection = self.notifs_handler.current_selection(ctx.guild.id)
            notif_setting = self.notifs_handler.get_notif_setting_by_id(ctx.guild.id, current_selection)

        if notif_setting == None:
            await ctx.send("", embed=self.invalid_selection_embed)
            return

        selection_local_id = self.notifs_handler.parse_id_to_local(ctx.guild.id, current_selection)
        confirmation_message = await ctx.send(
            "",
            embed=generate_embed(
                title="Stream Notifications - Deletion Confirmation",
                description=f"**Are you sure you want to delete the notifications for the following channel?:**\nSetting #{selection_local_id + 1} - Channel: <#{notif_setting.channel_id}>\n\nTo confirm, react with the following within the next 30 seconds: ✅",
                footer_text=f"Requested by {ctx.author}",
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
            await confirmation_message.edit(embed=generate_embed(
                title="Stream Notifications - Deletion",
                description="No confirmation was given within 30 seconds.",
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message,
            ))
        else:
            try:
                # Attempt to delete the webhook.
                async with ClientSession() as session:
                    webhook = discord.Webhook.from_url(notif_setting.webhook_url, adapter=discord.AsyncWebhookAdapter(session))
                    await webhook.delete(reason="Deleting via command.")
            except Exception as e:
                print(e)
                pass
            finally:
                # Delete the setting from the database.
                self.bot.db_session.delete(notif_setting)
                self.bot.db_session.commit()

            await confirmation_message.edit(embed=generate_embed(
                title="Stream Notifications - Succesful Deletion",
                description=f"Succesfully deleted Setting #{selection_local_id + 1} on channel: <#{notif_setting.channel_id}>.",
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message,
            ))

    @streamnotifs.error
    async def streamnotifs_error(self, ctx, error):
        if isinstance(error, commands.errors.BotMissingPermissions):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description=dedent("""
                        **The bot requires the following permission for stream notifications: 'Manage Webhooks'**
                        We've recently changed the way that stream notifs work, which means that they will need to be resetup once you enable this permission.
                        **If you'd like any assistance in setting up notifications, we're happy to help out.**
                        Just reach out to us in our support guild found by doing '{prefix}support'
                    """).strip().format(prefix=self.bot.get_relevant_prefix(ctx.message)),
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        elif isinstance(error, commands.errors.CheckFailure):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="You aren't authorised to use this.\nYou require the following permission: 'Manage Guild'",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        elif isinstance(error, GuildNotifsLimitExceeded):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="You are currently at the guild notification channel list.\nEither delete/modify an existing notification setting.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="Something else went wrong. The error has been reported.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

def setup(bot):
    bot.add_cog(Management(bot))
