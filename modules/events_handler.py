# General Events Handler
import discord
from discord.ext import commands

from utils.helpers import generate_embed
from utils.classes import BroadcastNotifSettingsHandler
from utils.settings import get_error_channel, get_join_leave_channel

class EventsHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.notif_settings_handler = BroadcastNotifSettingsHandler()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # Ignore if the exception is command not found.
        if isinstance(error, commands.CommandNotFound):
            return

        # Log the exception.
        print(error)
        self.bot.sentry.capture_exception(error)

        # Return if there is already an error handler for this command.
        if hasattr(ctx.command, "on_error"):
            return

        # Send a message to an error channel.
        error_log_channel = await self.bot.fetch_channel(get_error_channel())
        if isinstance(error, commands.CheckFailure):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Insufficient Permissions", color=discord.Color(0x8B0000),
                ),
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Error - Missing Argument",
                    description=f"Missing the following required argument: '{error.param.name}'.",
                    color=discord.Color(0x8B0000),
                    footer_text="Caused by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await error_log_channel.send(
                "",
                embed=generate_embed(
                    title="Command Error Report",
                    fields={
                        "Error Type": type(error.original).__name__,
                        "Arguments": "\n".join(error.original.args),
                        "Invoking User": f"{ctx.author} ({ctx.author.id})",
                        "Invoking Message": ctx.message.content,
                        "Guild": f"{ctx.guild.name} ({ctx.guild.id})",
                    },
                    color=discord.Color(0x8B0000),
                    footer_text="None",
                ),
            )

            await ctx.send(
                "",
                embed=generate_embed(
                    title="An Error Occurred",
                    description="An error has occurred, but don't worry!\nA report has been sent to the developers.",
                    fields={
                        "Support Server": f"{self.bot.get_relevant_prefix(ctx.message)}support",
                        "Send Feedback": f"{self.bot.get_relevant_prefix(ctx.message)}feedback <message>",
                    },
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        # Send a message to the guild join log.
        join_channel = await self.bot.fetch_channel(get_join_leave_channel())
        await join_channel.send(
            "",
            embed=generate_embed(
                title=f"Joined {guild.name}",
                description=f"Now in {len(self.bot.guilds)} guilds.",
                color=discord.Color(0x32CD32),
                fields={
                    "Owner": f"{guild.owner}\n({guild.owner_id})",
                    "Guild ID": f"{guild.id}",
                    "Member Count": f"{guild.member_count}",
                },
                thumbnail=guild.icon_url,
                footer_text="None",
                bot=self.bot,
            ),
        )

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        # Delete any settings that the guild had.
        notification_settings = self.notif_settings_handler.get_notif_settings(guild.id)
        if notification_settings != None:
            for notif_setting in notification_settings:
                self.bot.db_session.delete(notif_setting)
        self.bot.set_server_prefix(guild.id)

        # Send a message to the guild leave log.
        leave_channel = await self.bot.fetch_channel(get_join_leave_channel())
        await leave_channel.send(
            "",
            embed=generate_embed(
                title=f"Left {guild.name}",
                description=f"Now in {len(self.bot.guilds)} guilds.",
                color=discord.Color(0x8B0000),
                fields={
                    "Owner": f"{guild.owner}\n({guild.owner_id})",
                    "Guild ID": f"{guild.id}",
                    "Member Count": f"{guild.member_count}",
                },
                thumbnail=guild.icon_url,
                footer_text="None",
                bot=self.bot,
            ),
        )

def setup(bot):
    bot.add_cog(EventsHandler(bot))
