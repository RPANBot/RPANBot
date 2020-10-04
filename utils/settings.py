from os import getenv
from yaml import safe_load
from dotenv import load_dotenv

class Settings:
    def __init__(self, file_path: str) -> None:
        """
        Load the required configuration files.
        :param file_path: The path to the main project folder.
        """

        # Load the env file.
        load_dotenv(dotenv_path=f"{file_path}/.env", verbose=True)

        # Load the YAML config.
        self.load_config(file_path)

        # Load the subclasses.
        self.ids = self.IDs(self)
        self.links = self.Links(self)
        self.reddit = self.Reddit(self)

        print("Succesfully loaded the settings.")

    def load_config(self, file_path: str) -> None:
        """
        Load the YAML configuration file.
        :param file_path: The path to the config's folder.
        """
        self.config = {}
        try:
            with open(f"{file_path}/config.yml", "r") as config_file:
                self.config = safe_load(config_file.read())
        except Exception as e:
            print(f"{e} - Problem loading the config file.")
            exit()

        # Parse the config.
        self.config["rpan_subreddits"]["list"] = list(set([
            subreddit.lower()
            for subreddit in self.config["rpan_subreddits"]["list"]
        ] + [
            "pan",
            "animalsonreddit",
            "distantsocializing",
            "glamourschool",
            "headlineworthy",
            "readwithme",
            "redditinthekitchen",
            "redditmasterclasses",
            "redditsessions",
            "shortcircuit",
            "tabletoplive",
            "talentshow",
            "theartiststudio",
            "thegamerlounge",
            "theyoushow",
            "whereintheworld",
        ]))
        self.config["rpan_subreddits"]["abbreviations"] = dict(
            (abbreviation.lower(), subreddit.lower())
            for abbreviation, subreddit in self.config["rpan_subreddits"]["abbreviations"].items()
        )
        self.config["rpan_subreddits"]["abbreviations"].update({
            "aor": "animalsonreddit",
            "ds": "distantsocializing",
            "gs": "glamourschool",
            "hw": "headlineworthy",
            "rwm": "readwithme",
            "ritk": "redditinthekitchen",
            "rmc": "redditmasterclasses",
            "rs": "redditsessions",
            "sc": "shortcircuit",
            "ttl": "tabletoplive",
            "ts": "talentshow",
            "tas": "theartiststudio",
            "tgl": "thegamerlounge",
            "tys": "theyoushow",
            "witw": "whereintheworld",
        })
        self.config["mqmm_notifications"] = dict(
            (subreddit.lower(), channel_id)
            for subreddit, channel_id in self.config["mqmm_notifications"].items()
        )

    class Reddit:
        def __init__(self, parent) -> None:
            self.parent = parent

        @property
        def auth_info(self) -> dict:
            return {
                "client_id": getenv("REDDIT_CLIENT_ID"),
                "client_secret": getenv("REDDIT_CLIENT_SECRET"),
                "refresh_token": getenv("REDDIT_REFRESH_TOKEN"),
            }

        @property
        def mqmm_settings(self) -> dict:
            return self.parent.config["mqmm_notifications"]

        @property
        def rpan_subreddits(self) -> list:
            return self.parent.config["rpan_subreddits"]["list"]

        @property
        def rpan_sub_abbreviations(self) -> dict:
            return self.parent.config["rpan_subreddits"]["abbreviations"]

    class IDs:
        def __init__(self, parent) -> None:
            self.parent = parent

        @property
        def rpan_guilds(self) -> list:
            return self.parent.config["rpan_guilds"]

        @property
        def support_guilds(self) -> list:
            return self.parent.config["bot_support_guilds"]

        @property
        def bot_developers(self) -> list:
            return self.parent.config["bot_developer_ids"]

        @property
        def join_leave_channel(self) -> int:
            return getenv("BOT_JOIN_LEAVE_CHANNEL")

        @property
        def error_channel(self) -> int:
            return getenv("BOT_ERROR_CHANNEL")

        @property
        def bug_reports_channel(self) -> int:
            return getenv("BOT_BUG_REPORTS_CHANNEL")

        @property
        def approved_bugs_channel(self) -> int:
            return getenv("BOT_APPROVED_BUGS_CHANNEL")

        @property
        def denied_bugs_channel(self) -> int:
            return getenv("BOT_DENIED_BUGS_CHANNEL")

    class Links:
        def __init__(self, parent) -> None:
            self.parent = parent

            self.bot_avatar = "https://i.imgur.com/Ayj5squ.png"
            self.bot_invite = "https://discord.com/oauth2/authorize?client_id=710945234892095559&scope=bot&permissions=537095232"
            self.support_guild = "https://discord.gg/DfBp4x4"

        @property
        def sentry(self) -> str:
            return getenv("SENTRY_LINK")

    @property
    def default_prefix(self) -> str:
        return getenv("BOT_PREFIX")

    @property
    def statuspage_key(self) -> str:
        return getenv("STATUSPAGE_API_KEY")

    @property
    def discord_key(self) -> str:
        return getenv("BOT_DISCORD_KEY")

def init_settings(path) -> Settings:
    global loaded_settings
    loaded_settings = Settings(path)
    return loaded_settings

def get_settings() -> Settings:
    return loaded_settings
