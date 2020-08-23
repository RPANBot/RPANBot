import discord
from discord.ext import commands

from os import path
from glob import glob
from pygount import ProjectSummary, SourceAnalysis

from traceback import print_exc
from logging import WARNING, FileHandler, Formatter, getLogger

from modules.utils.helpers import generate_embed
from modules.utils.sentry import init_sentry, get_sentry
from modules.utils.database import GuildPrefix, get_db_session
from modules.utils.settings import load_configs, get_discord_key, get_default_prefix, get_sentry_link, get_error_channel, get_join_leave_channel

class RPANBot(commands.Bot):
    def __init__(self):
        # Load the configuration files.
        load_configs(path.dirname(path.abspath(__file__)))

        # Initiate the bot instance.
        super().__init__(
            command_prefix=self.get_trigger_prefix,
            description="RPANBot",
            case_insensitive=True,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"RPAN | {get_default_prefix()}help",
                emoji={
                    "id": 726972051432144898,
                    "name": "rpan",
                },
            ),
        )

        # Start logging.
        logger = getLogger("discord")
        logger.setLevel(WARNING)
        handler = FileHandler(filename="discord.log", encoding="utf-8", mode="w")
        handler.setFormatter(Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        logger.addHandler(handler)

        # Initiate sentry.
        init_sentry(get_sentry_link())
        self.sentry = get_sentry()

        # Calculate the lines of code.
        self.calculate_lines_of_code()

        # Load all the modules.
        for module_name in [module.replace(".py","") for module in map(path.basename, glob("modules/*.py"))]:
            try:
                self.load_extension(f"modules.{module_name}")
                print(f"MODULES - Loaded '{module_name}'.")
            except Exception as e:
                print(f"MODULES - Failed to load '{module_name}'.")
                print_exc()
                pass

        # Make the bot type before sending command responses.
        self.before_invoke(self.before_command)

        # Run the bot.
        self.run(get_discord_key())

    async def on_ready(self):
        print("Succesfully logged in!")

    def get_trigger_prefix(self, bot, message=None):
        if message == None:
            return get_default_prefix()

        try:
            result = get_db_session().query(GuildPrefix).filter(GuildPrefix.guild_id==message.guild.id).first()
            prefix = get_default_prefix() if result == None else result.guild_prefix
            return commands.when_mentioned_or(prefix)(self, message)
        except:
            return commands.when_mentioned_or(get_default_prefix())(self, message)

    def get_relevant_prefix(self, message=None):
        prefix = self.get_trigger_prefix(self, message)
        if isinstance(prefix, str):
            return prefix
        else:
            return prefix[2]

    def set_server_prefix(self, server, prefix):
        guild_id = 0
        if isinstance(server, int):
            guild_id = server
        else:
            guild_id = server.id

        if prefix != get_default_prefix():
            prefixSetting = GuildPrefix(
                guild_id=guild_id,
                guild_prefix=prefix,
            )

            get_db_session().merge(prefixSetting)
            get_db_session().commit()
        else:
            # Prefix is set to the default, so we don't need a record anymore.
            get_db_session().query(GuildPrefix).filter_by(guild_id=guild_id).delete()
            get_db_session().commit()

    def calculate_lines_of_code(self):
        project_summary = ProjectSummary()
        for source_path in glob("**/*.py", recursive=True):
            source_analysis = SourceAnalysis.from_file(source_path, "pygount", encoding="utf-8", fallback_encoding="cp437")
            project_summary.add(source_analysis)

        self.lines_of_code = 0
        for language_summary in project_summary.language_to_language_summary_map.values():
            self.lines_of_code += language_summary.code_count

    async def before_command(self, ctx):
        await ctx.trigger_typing()

    async def on_guild_join(self, guild):
        join_channel = await self.fetch_channel(get_join_leave_channel())
        await join_channel.send(
            "",
            embed=generate_embed(
                title="Joined {}".format(guild.name),
                color=discord.Color(0x32CD32),
                fields={
                    "Owner": f"{guild.owner}\n({guild.owner_id})",
                    "Guild ID": "{}".format(guild.id),
                    "Member Count": "{}".format(guild.member_count),
                },
                thumbnail=guild.icon_url,
                footer_text="None",
            ),
        )

    async def on_guild_remove(self, guild):
        leave_channel = await self.fetch_channel(get_join_leave_channel())
        await leave_channel.send(
            "",
            embed=generate_embed(
                title=f"Left {guild.name}",
                color=discord.Color(0x8B0000),
                fields={
                    "Owner": f"{guild.owner}\n({guild.owner_id})",
                    "Guild ID": f"{guild.id}",
                    "Member Count": f"{guild.member_count}",
                },
                thumbnail=guild.icon_url,
                footer_text="None",
            ),
        )

    async def on_command_error(self, ctx, error):
        # Ignore if the exception is command not found.
        if isinstance(error, commands.CommandNotFound):
            return

        # Log the exception.
        print(error)
        self.sentry.capture_exception(error)

        # Return if there is already an error handler for this command.
        if hasattr(ctx.command, "on_error"):
            return

        error_log_channel = await self.fetch_channel(get_error_channel())
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
                    bot=self,
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
                        "Support Server": f"{self.get_relevant_prefix(ctx.message)}support",
                        "Send Feedback": f"{self.get_relevant_prefix(ctx.message)}feedback <message>",
                    },
                    color=discord.Color(0x8B0000),
                ),
            )

# Initiate the bot.
RPANBot()
