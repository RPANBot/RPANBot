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
from quart import current_app, session

from discord import Permissions
from discord.utils import get

from functools import cached_property
from cachetools.func import ttl_cache


class Guild:
    def __init__(self, payload: dict) -> None:
        self.id = int(payload["id"])
        self.name = payload["name"]
        self.icon = payload["icon"]

    @cached_property
    def bot_guild(self) -> bool:
        guild = get(current_app.core.bot.guilds, id=self.id)
        if guild:
            return True
        else:
            return False

    @ttl_cache(maxsize=128, ttl=120)
    def user_has_access(self) -> None:
        user = current_app.user_handler.get_user()

        guild = get(current_app.core.bot.guilds, id=self.id)
        if guild is None:
            return False

        guild_member = guild.get_member(user.id)
        if guild_member is None:
            return False
        else:
            perms = guild_member.guild_permissions
            if perms.manage_guild:
                return True
            else:
                return False


class User:
    def __init__(self, user_payload: dict, guilds_payload: dict) -> None:
        self.id = int(user_payload["id"])
        self.tag = "{username}#{discrim}".format(username=user_payload["username"], discrim=user_payload["discriminator"])
        self.is_real = True

        self.refreshed_before = False

        self.process_guilds(guilds_payload)

    def process_guilds(self, guilds_payload: dict) -> None:
        """
        Processes the user's guilds on initiation.
        """
        self.guilds_mapping = {}
        for guild_info in guilds_payload:
            # Only store guilds where the user has Manage Guild permissions. (this is also the permission required to change settings)
            perms = Permissions(permissions=guild_info["permissions"])
            if perms.manage_guild:
                self.guilds_mapping[int(guild_info["id"])] = Guild(guild_info)

        self.guilds = sorted(self.guilds_mapping.values(), key=lambda g: g.bot_guild, reverse=True)

    def refresh(self) -> None:
        """
        Refresh a user's guild list, and the user themselves.
        """
        if not self.refreshed_before:
            self.refreshed_before = True
            discord = current_app.user_handler.base_session(token=session["DISCORD_TOKEN"])

            user_payload = discord.get("https://discord.com/api/users/@me").json()
            loaded_tag = "{username}#{discrim}".format(username=user_payload["username"], discrim=user_payload["discriminator"])
            if loaded_tag != self.tag:
                self.tag = loaded_tag

            guilds_payload = discord.get("https://discord.com/api/users/@me/guilds").json()
            self.process_guilds(guilds_payload)


class UnauthedUser:
    def __init__(self) -> None:
        self.is_real = False
