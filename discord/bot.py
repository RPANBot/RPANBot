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
from discord import Activity, ActivityType, Intents, TextChannel, Guild
from discord.ext.commands import Bot, check, when_mentioned_or

from typing import Union

from traceback import print_exc

from expiringdict import ExpiringDict

from utils.database.models.exclusions import ExcludedUser
from utils.database.models.custom_prefixes import CustomPrefixes


class RPANBot(Bot):
    def __init__(self, core) -> None:
        self.core = core

        bot_intents = Intents.default()
        bot_intents.members = True

        super().__init__(
            command_prefix=self.get_trigger_prefix,
            description="RPANBot: A bot helping link Discord and RPAN.",

            case_insensitive=True,
            intents=bot_intents,

            activity=Activity(
                type=ActivityType.watching,
                name="RPAN | rpanbot.botcavern.xyz",
            ),
        )

        # Start a database session.
        self.db_session = self.core.db_handler.Session()

        # Load the modules.
        self.module_prefix = "discord.modules.{name}"
        modules = [
            "general",
            "rpan",
            "events",
            "management",
            "developer",
            "notifications_watcher",
            "help_command",
            "tasks",
        ]

        for module in modules:
            try:
                self.load_extension(self.module_prefix.format(name=module))
                print(f"DISCORD: Loaded {module}.")
            except Exception:
                print(f"DISCORD: Failed to load {module}.")
                print_exc()

        # Initiate some of the caches.
        self.prefix_cache = ExpiringDict(max_len=25, max_age_seconds=1800)
        self.excluded_user_cache = ExpiringDict(max_len=25, max_age_seconds=600)

    def get_prefixes(self, guild: Guild) -> list:
        if guild is None:
            return self.core.settings.discord.default_prefixes

        if guild.id in self.prefix_cache:
            return self.prefix_cache[guild.id]
        else:
            result = self.db_session.query(CustomPrefixes).filter_by(guild_id=guild.id).first()
            if result is None:
                self.prefix_cache[guild.id] = self.core.settings.discord.default_prefixes
                return self.prefix_cache[guild.id]
            else:
                self.prefix_cache[guild.id] = result.prefixes
                return self.prefix_cache[guild.id]

    def get_trigger_prefix(self, bot, message=None):
        """
        Get the trigger prefixes for a command (from a message).
        :return: The prefixes that the bot should respond to for that message.
        """
        if message is None:
            return self.core.settings.discord.default_prefixes

        prefixes_to_use = self.get_prefixes(message.guild)
        return when_mentioned_or(*prefixes_to_use)(self, message)

    def is_excluded_user(self, user_id: int) -> bool:
        """
        Checks if a user is excluded from using the bot.
        :return: If they are or not.
        """
        if user_id in self.excluded_user_cache:
            return self.excluded_user_cache[user_id]

        result = self.db_session.query(ExcludedUser).filter_by(user_id=user_id).first()
        if result:
            self.excluded_user_cache[user_id] = True
        else:
            self.excluded_user_cache[user_id] = False

        return self.excluded_user_cache[user_id]

    async def on_ready(self) -> None:
        print("DISCORD: Started bot.")
        await self.fetch_user_count()

    async def fetch_user_count(self) -> None:
        """
        Fetches the total number of users in the guilds that RPANBot is in.
        """
        await self.wait_until_ready()

        self.user_count = 0
        for member in self.get_all_members():
            self.user_count += 1

    async def find_channel(self, id: int) -> Union[TextChannel, None]:
        """
        Find a channel by its id. If the channel isn't in the cache then fetch it.
        :return: The channel found or None.
        """
        channel = self.get_channel(id)
        if channel is None:
            channel = await self.fetch_channel(id)
        return channel

    def start_bot(self) -> None:
        self.run(self.core.settings.discord.token)
