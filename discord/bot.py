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
from discord import Activity, ActivityType, TextChannel
from discord.ext.commands import Bot

from typing import Union

from traceback import print_exc


class RPANBot(Bot):
    def __init__(self, core) -> None:
        self.core = core

        super().__init__(
            command_prefix=self.core.settings.discord.default_prefix,
            description="RPANBot: A bot helping link Discord and RPAN.",
            case_insensitive=True,
            activity=Activity(
                type=ActivityType.watching,
                name="RPAN | rpanbot.botcavern.xyz",
            ),
        )

        # Load the modules.
        self.module_prefix = "discord.modules.{name}"
        modules = [
            "general",
        ]

        for module in modules:
            try:
                self.load_extension(self.module_prefix.format(name=module))
                print(f"DISCORD: Loaded {module}.")
            except Exception:
                print(f"DISCORD: Failed to load {module}.")
                print_exc()

    def start_bot(self) -> None:
        self.run(self.core.settings.discord.token)

    async def on_ready(self) -> None:
        print("DISCORD: Started bot.")
        await self.fetch_user_count()

    async def fetch_user_count(self) -> None:
        """
        Fetches the total number of unique users in the guilds that RPANBot is in.
        """
        await self.wait_until_ready()

        users = []
        for guild in self.guilds:
            async for member in guild.fetch_members(limit=None):
                if member.id not in users:
                    users.append(member.id)
        self.user_count = len(users)

    async def find_channel(self, id: int) -> Union[TextChannel, None]:
        """
        Find a channel by its id. If the channel isn't in the cache then fetch it.
        :return: The channel found or None.
        """
        channel = self.get_channel(id)
        if channel is None:
            channel = await self.fetch_channel(id)
        return channel
