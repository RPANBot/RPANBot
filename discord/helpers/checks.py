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
from typing import Union

from discord.helpers.exceptions import DeveloperCheckFailure, ExcludedUserBlocked


async def is_core_developer(ctx) -> Union[bool, DeveloperCheckFailure]:
    """
    Checks if a user is a core bot developer.
    :return: True or DeveloperCheckFailure is raised.
    """
    if ctx.author.id in ctx.bot.core.settings.ids.bot_developers:
        return True
    raise DeveloperCheckFailure


async def is_rpan_guild(ctx) -> bool:
    """
    Checks if the guild is an RPAN discord guild.
    :return: Whether or not it is (as listed in the settings).
    """
    if not ctx.guild:
        return False
    return ctx.guild.id in ctx.bot.core.settings.ids.rpan_guilds


async def is_not_excluded(ctx) -> Union[bool, ExcludedUserBlocked]:
    """
    Checks if the author is banned from using the bot.
    :return: True if they are not, and ExcludedUserBlocked is raised if they are.
    """
    if not ctx.bot.is_excluded_user(ctx.author.id):
        return True
    else:
        raise ExcludedUserBlocked
