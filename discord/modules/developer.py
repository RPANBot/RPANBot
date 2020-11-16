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
from discord import Activity, ActivityType, Status, TextChannel, Member, User
from discord.ext.commands import Cog, command, check, group

from os import execl
from sys import executable, argv

from typing import Optional, Union

from discord.helpers.checks import is_core_developer
from discord.helpers.generators import RPANEmbed

from utils.database.models.exclusions import ExcludedGuild, ExcludedUser


class Developer(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @group(aliases=["dev"])
    @check(is_core_developer)
    async def developer(self, ctx) -> None:
        """
        Core Development Commands
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="RPAN Developer Commands",
                    description="An invalid/no subcommand was input.",

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @developer.group(name="load")
    async def developer_load(self, ctx, name) -> None:
        """
        DEVELOPER: Load a bot extension.
        """
        try:
            self.bot.load_extension(self.bot.module_prefix.format(name=name))
        except Exception as e:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Loading",
                    description=f"Failed to load {name}.",
                    colour=0x8B0000,

                    fields={
                        "Exception Raised": str(e),
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        self.bot.core.calculate_loc()
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Development - Module Loading",
                description=f"Succesfully loaded {name}.",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @developer.group(name="unload")
    async def developer_unload(self, ctx, name) -> None:
        """
        DEVELOPER: Unload a bot extension.
        """
        try:
            self.bot.unload_extension(self.bot.module_prefix.format(name=name))
        except Exception as e:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Unloading",
                    description=f"Failed to unload {name}.",
                    colour=0x8B0000,

                    fields={
                        "Exception Raised": str(e),
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Development - Module Unloading",
                description=f"Succesfully unloaded {name}.",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @developer.group(name="reload")
    async def developer_reload(self, ctx, name) -> None:
        """
        DEVELOPER: Reload a bot extension.
        """
        try:
            self.bot.reload_extension(self.bot.module_prefix.format(name=name))
        except Exception as e:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Reload",
                    description=f"Failed to reload {name}.",
                    colour=0x8B0000,

                    fields={
                        "Exception Raised": str(e),
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        self.bot.core.calculate_loc()
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Development - Module Reload",
                description=f"Succesfully reloaded {name}.",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @developer.group(name="restart")
    async def developer_restart(self, ctx) -> None:
        """
        DEVELOPER: Restart the bot.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Development - Restarting Bot",
                user=ctx.author,
            )
        )

        await self.bot.change_presence(
            status=Status.idle,
            activity=Activity(
                type=ActivityType.watching,
                name="a restart.",
            )
        )

        try:
            await self.bot.logout()
        except Exception:
            pass
        finally:
            print("DEVELOPER: Restarting bot.")
            execl(executable, executable, *argv)

    @developer.group(name="leaveguild")
    async def developer_leaveguild(self, ctx, id: int) -> None:
        """
        Make the bot leave a specified guild.
        """
        guild = self.bot.get_guild(id)
        if guild is not None:
            await guild.leave()

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Left Guild",
                    fields={
                        "Name": guild.name,
                        "ID": id,
                        "Owner ID": guild.owner_id,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        else:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Failed to leave guild.",
                    description="No guild was found with that id.",
                    colour=0x8B0000,

                    fields={
                        "ID": id,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @developer.group(name="banguild")
    async def developer_banguild(self, ctx, id: int) -> None:
        """
        Ban a guild from inviting the bot.
        """
        guild = self.bot.get_guild(id)
        if guild is not None:
            await guild.leave()

        result = self.bot.db_session.query(ExcludedGuild).filter_by(guild_id=id).first()
        if result is None:
            self.bot.db_session.add(
                ExcludedGuild(
                    guild_id=id,
                )
            )
            self.bot.db_session.commit()

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Banned Guild",
                    fields={
                        "ID": id,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        else:
            self.bot.db_session.delete(result)
            self.bot.db_session.commit()

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Unbanned Guild",
                    description="This guild was already banned - the ban has been lifted.",
                    fields={
                        "ID": id,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @developer.group(name="banuser")
    async def developer_banuser(self, ctx, id: int) -> None:
        """
        Ban/unban a user from using the bot.
        """
        if id in self.bot.excluded_user_cache:
            del self.bot.excluded_user_cache[id]

        result = self.bot.db_session.query(ExcludedUser).filter_by(user_id=id).first()
        if result is None:
            self.bot.db_session.add(
                ExcludedUser(
                    user_id=id,
                )
            )
            self.bot.db_session.commit()

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Banned User",
                    fields={
                        "ID": id,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        else:
            self.bot.db_session.delete(result)
            self.bot.db_session.commit()

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Unbanned User",
                    description="This user is banned already - removing their ban.",

                    fields={
                        "ID": id,
                    },

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @developer.group(name="say")
    async def developer_say(self, ctx, channel: Optional[Union[TextChannel, Member, User]] = None, *, text: str):
        """
        Send a message as the bot to a specified member/user.
        """
        if channel is None:
            channel = ctx.channel

        try:
            await ctx.message.delete()
        except Exception:
            pass
        finally:
            await channel.send(text)


def setup(bot) -> None:
    bot.add_cog(Developer(bot))
