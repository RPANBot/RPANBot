# Server Management Module
from asyncio import sleep
from json import dumps, loads
from textwrap import dedent

import discord
from discord.ext import commands

from .utils.database import StreamNotifications, get_db_session
from .utils.helpers import generate_embed

class Management(commands.Cog, name="Server Management"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_guild_permissions(manage_guild=True)
    async def setprefix(self, ctx, *, prefix):
        """
        Set the bot prefix for the server
        """
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
                footer_text="Requested by {}".format(str(ctx.author)),
                bot=self.bot, message=ctx.message,
            )
        )

    @commands.group(aliases=["sn","broadcastnotifs","bn","streamannouncements","broadcastannouncements","streamnotifications","broadcastnotifications"], pass_context=True)
    @commands.has_guild_permissions(manage_guild=True)
    async def streamnotifs(self, ctx):
        """
        Setup notifications for a particular channel when specified users start streaming on RPAN.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications",
                    description="Configure notifications for when certain users go live on RPAN.\nEither you didn't enter a subcommand or that is an invalid subcommand.\n\nYou can find information on the specific commands by doing:\n{prefix}help streamnotifs SUBCOMMAND".format(prefix=self.bot.get_relevant_prefix(ctx.message)),
                    fields={
                        f"Subcommands ({self.bot.get_relevant_prefix(ctx.message)}streamnotifs SUBCOMMAND)": dedent("""
                            setup       Basic stream notifications setup.

                            setchannel  Set the channel of your stream notifications.
                            settext     Set some custom text (can include mentions) that comes with notifs.

                            adduser     Add a user to get stream notifs for.
                            removeuser  Remove a user from stream notifications.

                            addkeyword  Add a phrase/word that is needed in the title to send the notif. (Still checks users)
                            removekeyword  Removes a specific keyword/all required keywords (if nothing is specified).

                            delete      Delete stream notifs settings. (disables stream notifications)

                            settings    View the current stream notification settings here.
                        """),
                    },
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot, message=ctx.message,
                ),
            )

    @streamnotifs.group(pass_context=True, name="setup", help="Basic stream notifications setup (overrides previous settings).")
    async def streamnotifs_setup(self, ctx, username, channel):
        channelId = int("".join([char for char in channel if char.isdigit()]))

        isValidChannelId = False
        if len(str(channelId)) >= 16:
            if channelId in [text_channel.id for text_channel in ctx.guild.text_channels]:
                isValidChannelId = True

        if isValidChannelId:
            hasChannelPermissions = False
            try:
                fetched_channel = await self.bot.fetch_channel(channelId)
                permissionsCheckMsg = await fetched_channel.send("Stream Notifications - Testing bot channel permissions.")
                hasChannelPermissions = True
                await permissionsCheckMsg.delete()
            except Exception as e:
                print(repr(e) + " - Problem testing bot channel perms.")
                pass

            await sleep(100)

            if hasChannelPermissions:
                username = username.replace("/u/","").replace("u/","").lower()

                try:
                    notificationsSettings = StreamNotifications(
                        guild_id=ctx.guild.id,
                        notifications_usernames=dumps([username]),
                        notifications_channel_id=channelId,
                    )

                    get_db_session().merge(notificationsSettings)
                    get_db_session().commit()

                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="Notifications will now be sent (in <#{channel}>) when the following user goes live: ``u/{user}``.\nTo customize this more have a look at the commands in '{prefix}streamnotifs'.".format(channel=channelId, user=username, prefix=self.bot.get_relevant_prefix(ctx.message)),
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                except:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications - Error",
                            description="There was a problem saving these settings. The bot developers have been notified of the issue.",
                            color=discord.Color(0x8B0000),
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                    raise
            else:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications - Error",
                        description="The bot doesn't have permissions to post in that channel.",
                        color=discord.Color(0x8B0000),
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="That isn't a valid text channel. Is it on this Discord guild? Does it exist?",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )

    @streamnotifs.group(pass_context=True, name="adduser", aliases=["add"], help="Add a user to get stream notifications from.")
    async def streamnotifs_adduser(self, ctx, username):
        try:
            result = get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).first()
            if result != None:
                # Record Exists
                username = username.replace("/u/","").replace("u/","").lower()

                currentUsers = result.notifications_usernames
                if currentUsers in [None, ""]:
                    currentUsers = "[]"

                currentUsers = loads(currentUsers)
                if username not in currentUsers:
                    currentUsers.append(username)

                    notificationsSettings = StreamNotifications(
                        guild_id=ctx.guild.id,
                        notifications_usernames=dumps(currentUsers),
                    )

                    get_db_session().merge(notificationsSettings)
                    get_db_session().commit()

                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="Succesfully added that user to the stream notifications.",
                            fields={
                                "New User": "``u/{}``".format(username)
                            },
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                else:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="That user is already in the stream notifications for this guild.",
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
            else:
                # The guild has no other stream notification settings.
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications",
                        description="Please set a stream notifications channel before trying to add a user.",
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There was a problem saving this setting. The bot developers have been notified of the issue.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @streamnotifs.group(pass_context=True, name="removeuser", aliases=["remuser", "remove"], help="Remove a user from stream notifications for this guild.")
    async def streamnotifs_removeuser(self, ctx, username):
        try:
            result = get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).first()
            if result != None:
                # Record Exists
                username = username.replace("/u/","").replace("u/","").lower()
                currentUsers = result.notifications_usernames
                if currentUsers == None:
                    currentUsers = ""

                currentUsers = loads(currentUsers)
                if username in currentUsers:
                    currentUsers.remove(username)

                    notificationsSettings = StreamNotifications(
                        guild_id=ctx.guild.id,
                        notifications_usernames=dumps(currentUsers),
                    )

                    get_db_session().merge(notificationsSettings)
                    get_db_session().commit()

                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="You will no longer receive stream notifications for that user.",
                            fields={
                                "Removed User": "``u/{}``".format(username)
                            },
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                else:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="That user wasn't in the stream notification settings.",
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
            else:
                # The guild has no other stream notification settings.
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications",
                        description="This guild doesn't currently have stream notifications setup.",
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There was a problem saving this setting. The bot developers have been notified of the issue.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @streamnotifs.group(pass_context=True, name="addkeyword", aliases=["addphrase", "setphrase"], help="""
    Add a phrase/word that is needed in the title to send a notifications.

    Note: This is optional. When any of the added users go live it will check for this keyword in the title.

    Having multiple means that if any of the individual phrases are in the title, it will send notifications.
    """)
    async def streamnotifs_addkeyword(self, ctx, *, keyword):
        try:
            result = get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).first()
            if result != None:
                # Record Exists
                keyword = keyword.lower()

                currentKeywords = result.notifications_keywords
                if currentKeywords in [None, ""]:
                    currentKeywords = "[]"

                currentKeywords = loads(currentKeywords)
                if keyword not in currentKeywords:
                    currentKeywords.append(keyword)

                    notificationsSettings = StreamNotifications(
                        guild_id=ctx.guild.id,
                        notifications_keywords=dumps(currentKeywords),
                    )

                    get_db_session().merge(notificationsSettings)
                    get_db_session().commit()

                    wordOrPhrase = "word" if len(keyword.split(" ")) == 1 else "phrase"
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="Succesfully added that {} as a required keyword.\nIf any of the current individual phrases are in the title, it will send notifications.".format(wordOrPhrase),
                            fields={
                                "New {}".format(wordOrPhrase.capitalize()): "``{}``".format(keyword)
                            },
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                else:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="That phrase/word is already in the keywords for this guild.",
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
            else:
                # The guild has no other stream notification settings.
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications",
                        description="Please set a stream notifications channel before trying to do this.",
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There was a problem saving this setting. The bot developers have been notified of the issue.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @streamnotifs.group(pass_context=True, name="removekeyword", aliases=["removephrase", "deletekeyword", "deletephrase", "removekeywords", "deletekeywords", "deletephrases", "removephrases"], help="Remove a specific keyword/all required keywords. If nothing is specified it will delete them all.")
    async def streamnotifs_removekeyword(self, ctx, *, keyword="[ALL_-_KEYWORDS]"):
        try:
            result = get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).first()
            if result != None:
                # Record Exists
                keyword = keyword.lower()

                currentKeywords = result.notifications_keywords
                if currentKeywords in [None, ""]:
                    currentKeywords = "[]"

                currentKeywords = loads(currentKeywords)
                if keyword in currentKeywords or keyword == "[all_-_keywords]":
                    allKeywords = False
                    if keyword == "[all_-_keywords]":
                        allKeywords = True
                        currentKeywords = []
                    else:
                        currentKeywords.remove(keyword)

                    notificationsSettings = StreamNotifications(
                        guild_id=ctx.guild.id,
                        notifications_keywords=dumps(currentKeywords),
                    )

                    get_db_session().merge(notificationsSettings)
                    get_db_session().commit()

                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="Succesfully removed {}.".format("that as a keyword" if not allKeywords else "all keywords"),
                            fields={
                                "Removed {}".format("Phrase/Word" if not allKeywords else "All"): "``{}``".format(keyword if not allKeywords else "Phrase(s)/Word(s)")
                            },
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                else:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="That phrase/word is not in the keywords for this guild.",
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
            else:
                # The guild has no other stream notification settings.
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications",
                        description="You have not setup stream notifications. There are no keywords to remove.",
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There was a problem saving this setting. The bot developers have been notified of the issue.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @streamnotifs.group(pass_context=True, name="setchannel", help="Set the channel of your stream notifications.")
    async def streamnotifs_setchannel(self, ctx, channel):
        channelId = "".join([char for char in channel if char.isdigit()])
        if channelId != "":
            channelId = int(channelId)
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="You input an invalid channel, the correct way is to use the # of a channel.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            return

        isValidChannelId = False
        if len(str(channelId)) >= 16:
            if channelId in [text_channel.id for text_channel in ctx.guild.text_channels]:
                isValidChannelId = True

        if isValidChannelId:
            hasChannelPermissions = False
            try:
                fetched_channel = await self.bot.fetch_channel(channelId)
                permissionsCheckMsg = await fetched_channel.send("Stream Notifications - Testing bot channel permissions.")
                hasChannelPermissions = True
                await permissionsCheckMsg.delete()
            except Exception as e:
                print(repr(e) + " - Problem testing bot channel perms.")
                pass

            await sleep(100)

            if hasChannelPermissions:
                try:
                    result = get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).first()
                    if result != None:
                        notificationsSettings = StreamNotifications(
                            guild_id=ctx.guild.id,
                            notifications_channel_id=channelId,
                        )

                        get_db_session().merge(notificationsSettings)
                        get_db_session().commit()

                        await ctx.send(
                            "",
                            embed=generate_embed(
                                title="Stream Notifications",
                                description="Your stream notification channel has been changed to <#{channel}>.".format(channel=channelId),
                                footer_text="Requested by {}".format(str(ctx.author)),
                                bot=self.bot,
                                message=ctx.message,
                            ),
                        )
                    else:
                        notificationsSettings = StreamNotifications(
                            guild_id=ctx.guild.id,
                            notifications_channel_id=channelId,
                        )

                        get_db_session().add(notificationsSettings)
                        get_db_session().commit()

                        await ctx.send(
                            "",
                            embed=generate_embed(
                                title="Stream Notifications",
                                description="Your stream notification channel has been changed to <#{channel}>.\nHowever, you don't have any other stream notification settings currently.".format(channel=channelId),
                                footer_text="Requested by {}".format(str(ctx.author)),
                                bot=self.bot,
                                message=ctx.message
                            ),
                        )
                except:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications - Error",
                            description="There was a problem saving this setting. The bot developers have been notified of the issue.",
                            color=discord.Color(0x8B0000),
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                    raise
            else:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications - Error",
                        description="The bot doesn't have permissions to post in that channel.",
                        color=discord.Color(0x8B0000),
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
                raise
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="That isn't a valid text channel. Is it on this Discord guild? Does it exist?",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )

    @streamnotifs.group(pass_context=True, name="settext", help="Set some custom text (can include mentions) for broadcast notifications.")
    async def streamnotifs_settext(self, ctx, *, text="none"):
        try:
            result = get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).first()
            if result != None:
                notificationsSettings = StreamNotifications(
                    guild_id=ctx.guild.id,
                    notifications_custom_text=text,
                )

                get_db_session().merge(notificationsSettings)
                get_db_session().commit()

                if text.lower() not in ["none","delete","remove","off"]:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="Your custom notification text has been changed.",
                            fields={
                                "New Custom Notification Text": "{}".format(text)
                            },
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                else:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="Stream Notifications",
                            description="Your custom notification text has been removed.",
                            footer_text="Requested by {}".format(str(ctx.author)),
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
            else:
                notificationsSettings = StreamNotifications(
                    guild_id=ctx.guild.id,
                    notifications_custom_text=text,
                )

                get_db_session().add(notificationsSettings)
                get_db_session().commit()

                if text == "":
                    text = "[TEXT HAS BEEN DELETED]"

                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications",
                        description="Your custom notification text has been changed.\nHowever, you don't have any other stream notification settings currently.",
                        fields={
                            "New Custom Notification Text": "{}".format(text)
                        },
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There was a problem saving this setting. The bot developers have been notified of the issue.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @streamnotifs.group(pass_context=True, name="settings", aliases=["info", "list"], help="View the stream notification settings for this guild.")
    async def streamnotifs_settings(self, ctx):
        try:
            result = get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).first()
            if result != None:
                usernames = loads(result.notifications_usernames)

                phrases = []
                try:
                    phrases = loads(result.notifications_keywords)
                except:
                    pass

                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications - Settings",
                        fields={
                            "Notifications for": (", ".join(["``u/{}``".format(username) for username in usernames]) if len(usernames) >= 1 else "None"),
                            "Notifications Channel": ("<#{channelId}> ({channelId})".format(channelId=result.notifications_channel_id) if result.notifications_channel_id not in [None, ""] else "None"),
                            "Custom Notifications Text": (result.notifications_custom_text if result.notifications_custom_text not in [None, ""] else "None"),
                            "(Title) Keyword Requirements": (" or ".join(["``{}``".format(phrase) for phrase in phrases]) if len(phrases) >= 1 else "None"),
                        },
                        footer_text="Requested by {} - Guild: {}".format(str(ctx.author), ctx.guild.id),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
            else:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Notifications",
                        description="There are no stream notification settings for this guild.",
                        footer_text="Requested by {}".format(str(ctx.author)),
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There was a problem getting the settings for this server. The bot developers have been notified of the issue.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @streamnotifs.group(pass_context=True, name="delete", help="Delete stream notifications from your guild (if you have them).")
    async def streamnotifs_delete(self, ctx):
        try:
            get_db_session().query(StreamNotifications).filter_by(guild_id=ctx.guild.id).delete()
            get_db_session().commit()

            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Deleted",
                    description="Your stream notification settings have been deleted for this guild (if there were any).",
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="There was a problem deleting the settings. The bot developers have been notified of the issue.",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @streamnotifs.error
    async def streamnotifs_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CheckFailure):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Notifications - Error",
                    description="You aren't authorised to use this.\nYou require the following permission: 'Manage Guild'",
                    color=discord.Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message
                ),
            )

def setup(bot):
    bot.add_cog(Management(bot))
