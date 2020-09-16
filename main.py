import discord
from discord.ext import commands

from os import path
from glob import glob
from traceback import print_exc
from pygount import ProjectSummary, SourceAnalysis

from traceback import print_exc
from logging import WARNING, FileHandler, Formatter, getLogger

from utils.sentry import init_sentry, get_sentry
from utils.database import GuildPrefix, get_db_session
from utils.settings import load_configs, get_discord_key, get_default_prefix, get_sentry_link

class RPANBot(commands.Bot):
    def __init__(self):
        # Load the configuration files.
        load_configs(path.dirname(path.abspath(__file__)))

        # Set the links to the support guild and inviting the bot.
        self.support_guild_link = "https://discord.gg/DfBp4x4"
        self.bot_avatar_link = "https://i.imgur.com/Ayj5squ.png"
        self.bot_invite_link = "https://discord.com/oauth2/authorize?client_id=710945234892095559&scope=bot&permissions=537095232"

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

        # Set the database session.
        self.db_session = get_db_session()

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
            result = self.db_session.query(GuildPrefix).filter(GuildPrefix.guild_id==message.guild.id).first()
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

    def set_server_prefix(self, server, prefix=None):
        guild_id = server if isinstance(server, int) else server.id
        if prefix == None:
            prefix = get_default_prefix()

        if prefix != get_default_prefix():
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
        project_summary = ProjectSummary()
        for source_path in glob("**/*.py", recursive=True):
            source_analysis = SourceAnalysis.from_file(source_path, "pygount", encoding="utf-8", fallback_encoding="cp437")
            project_summary.add(source_analysis)

        self.lines_of_code = 0
        for language_summary in project_summary.language_to_language_summary_map.values():
            self.lines_of_code += language_summary.code_count

    async def before_command(self, ctx):
        await ctx.trigger_typing()

# Initiate the bot.
RPANBot()
