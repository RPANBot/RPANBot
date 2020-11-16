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
from os import getenv

from yaml import safe_load

from dotenv import load_dotenv


class RPANBotSettings:
    def __init__(self, file_path: str = None) -> None:
        """
        Load the required configuration files.
        :param file_path: The path to the main project folder.
        """

        # Load the configs.
        config_path = file_path / "configs/"
        self.load_configs(config_path=config_path)
        self.load_environments(config_path=config_path)

        # Load the subclasses.
        self.ids = self.IDs(self)
        self.links = self.Links(self)

        self.web = self.Web(self)
        self.reddit = self.Reddit(self)
        self.discord = self.Discord(self)

        self.database = self.Database(self)

        print("Succesfully loaded the settings.")

    def load_configs(self, config_path: str) -> None:
        """
        Load the YAML configuration file.
        :param config_path: The path to the config's folder.
        """
        try:
            with open(config_path / "config.yml", "r") as file:
                self.config = safe_load(file.read())
        except Exception as e:
            print(f"SETTINGS: Problem loading the configuration files. - {e}")
            exit()

    def load_environments(self, config_path: str) -> None:
        """
        Load the bot environment file. (if it isn't already provided by Docker)
        :param config_path: The path to the environment file's folder.
        """
        if not getenv("BOT_DISCORD_KEY"):
            load_dotenv(dotenv_path=config_path / "bot.env", verbose=True)

    class Web:
        def __init__(self, parent) -> None:
            self.parent = parent

        @property
        def config(self) -> dict:
            return self.parent.config["web"]["config"]

        @property
        def redirect_uri(self) -> str:
            return self.parent.config["web"]["callbacks"]["login"]

    class Database:
        def __init__(self, parent) -> None:
            self.parent = parent

        @property
        def host(self) -> str:
            return self.parent.config["database"]["host"]

        @property
        def port(self) -> int:
            return self.parent.config["database"]["port"]

        @property
        def db(self) -> str:
            return self.parent.config["database"]["db"]

        @property
        def user(self) -> str:
            return self.parent.config["database"]["user"]

        @property
        def password(self) -> str:
            return self.parent.config["database"]["password"]

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
        def bot_developers(self) -> list:
            return self.parent.config["bot_developer_ids"]

        @property
        def join_leave_channel(self) -> int:
            return self.parent.config["channels"]["logs"]["join_leave"]

        @property
        def error_channel(self) -> int:
            return self.parent.config["channels"]["logs"]["error"]

        @property
        def bug_reports_channel(self) -> int:
            return self.parent.config["channels"]["bugs"]["reports"]

        @property
        def approved_bugs_channel(self) -> int:
            return self.parent.config["channels"]["bugs"]["approved"]

        @property
        def denied_bugs_channel(self) -> int:
            return self.parent.config["channels"]["bugs"]["denied"]

        @property
        def contact_channel(self) -> int:
            return self.parent.config["channels"]["developer"]["contact"]

        @property
        def exclusions_and_spam_channel(self) -> int:
            return self.parent.config["channels"]["developer"]["exclusions_and_spam"]

    class Links:
        def __init__(self, parent) -> None:
            self.parent = parent

            self.bot_avatar = "https://i.imgur.com/Ayj5squ.png"
            self.support_guild = "https://discord.gg/DfBp4x4"

        @property
        def sentry(self) -> str:
            return getenv("SENTRY_LINK")

    class Discord:
        def __init__(self, parent) -> None:
            self.parent = parent
            self.invite_permissions = 537095232

        @property
        def default_prefixes(self) -> list:
            return self.parent.config["default_prefixes"]

        @property
        def client_id(self) -> id:
            return getenv("DISCORD_CLIENT_ID")

        @property
        def client_secret(self) -> str:
            return getenv("DISCORD_CLIENT_SECRET")

        @property
        def token(self) -> str:
            return getenv("DISCORD_TOKEN")


loaded_instance = None
def Settings(*args, **kwargs) -> RPANBotSettings:
    global loaded_instance
    if not loaded_instance:
        loaded_instance = RPANBotSettings(*args, **kwargs)
    return loaded_instance
