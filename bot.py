import discord
from discord.ext import commands

from os import path
from glob import glob
from traceback import print_exc
from pygount import ProjectSummary, SourceAnalysis

from typing import Union

from traceback import print_exc
from logging import WARNING, FileHandler, Formatter, getLogger

from utils.reddit import RPANBotReddit
from utils.settings import init_settings
from utils.sentry import init_sentry, get_sentry
from utils.database import GuildPrefix, get_db_session

class RPANBot(commands.Bot):
    def __init__(self):
        # Load the configuration files.
        self.settings = init_settings(path.dirname(path.abspath(__file__)))

        # Initiate the Reddit instance.
        self.reddit = RPANBotReddit(self.settings)

        # Initiate the bot instance.
        super().__init__(
            command_prefix=self.get_trigger_prefix,
            description="RPANBot",
            case_insensitive=True,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"RPAN | {self.settings.default_prefix}help",
            ),
        )

        # Start logging.
        logger = getLogger("discord")
        logger.setLevel(WARNING)
        handler = FileHandler(filename="discord.log", encoding="utf-8", mode="w")
        handler.setFormatter(Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
        logger.addHandler(handler)

        # Initiate sentry.
        init_sentry(self.settings.links.sentry)
        self.sentry = get_sentry()

        # Set the database session.
        self.db_session = get_db_session()

        # Calculate the lines of code.
        self.calculate_lines_of_code()

        # Load all the modules.
        for module in [module.replace(".py", "") for module in map(path.basename, glob("modules/*.py"))]:
            try:
                self.load_extension(f"modules.{module}")
                print(f"MODULES: Loaded {module}.")
            except Exception as e:
                print(f"MODULES: Failed to load {module}.")
                print_exc()
                pass

        # Make the bot type before sending command responses.
        self.before_invoke(self.before_command)

        # Run the bot.
        self.run(self.settings.discord_key)

    async def on_ready(self):
        print("Succesfully logged in!")

    async def before_command(self, ctx):
        await ctx.trigger_typing()

    async def find_channel(self, id: int) -> Union[discord.TextChannel, None]:
        channel = self.get_channel(id)
        if channel == None:
            channel = await self.fetch_channel(id)
        return channel

    def get_trigger_prefix(self, bot, message=None):
        """
        Get the trigger prefix for a command (from a message).
        :return: The prefix(es) the bot should respond to for that message.
        """
        if message == None:
            return self.settings.default_prefix

        try:
            result = self.db_session.query(GuildPrefix).filter(GuildPrefix.guild_id==message.guild.id).first()
            prefix = get_default_prefix() if result == None else result.guild_prefix
            return commands.when_mentioned_or(prefix)(self, message)
        except:
            return commands.when_mentioned_or(self.settings.default_prefix)(self, message)

    def get_relevant_prefix(self, message=None):
        """
        Gets the text friendly version of a prefix.
        :return: The default or custom prefix.
        """
        prefix = self.get_trigger_prefix(self, message)
        if isinstance(prefix, str):
            return prefix
        else:
            return prefix[2]

    def set_server_prefix(self, server, prefix=None):
        """
        Sets the custom prefix of a guild.
        :param server: The guild to set the prefix on.
        :param prefix: The prefix to use.
        """
        guild_id = server if isinstance(server, int) else server.id
        if prefix == None:
            prefix = self.settings.default_prefix

        if prefix != self.settings.default_prefix:
            prefix_setting = GuildPrefix(
                guild_id=guild_id,
                guild_prefix=prefix,
            )

            self.db_session.merge(prefix_setting)
        else:
            # Prefix is set to the default, so we don't need a record anymore.
            self.db_session.query(GuildPrefix).filter_by(guild_id=guild_id).delete()
        self.db_session.commit()

    def calculate_lines_of_code(self):
        """
        Calculates the number of lines of code that the bot uses.
        """
        project_summary = ProjectSummary()
        for source_path in glob("**/*.py", recursive=True):
            source_analysis = SourceAnalysis.from_file(source_path, "pygount", encoding="utf-8", fallback_encoding="cp437")
            project_summary.add(source_analysis)

        self.lines_of_code = 0
        for language_summary in project_summary.language_to_language_summary_map.values():
            self.lines_of_code += language_summary.code_count
