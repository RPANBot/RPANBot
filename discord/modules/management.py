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
from discord.ext.commands import Cog, bot_has_permissions, command, group, guild_only, has_guild_permissions

from textwrap import dedent

from discord.helpers.generators import RPANEmbed

from utils.database.models.custom_prefixes import CustomPrefixes


def is_valid_prefix(prefix: str) -> bool:
    if not len(prefix) or len(prefix) >= 10:
        return False

    if "`" in prefix:
        return False

    return True


class Management(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.invalid_prefix_description = dedent("""
            That is an invalid prefix.

            ```md
            # Requirements:
            · the prefix should not contain: `
            · the prefix should not be blank
            · the prefix should be shorter than 10 characters
            ```
        """)

    def format_default_prefixes(self) -> str:
        return ", ".join([f"``{prefix}``" for prefix in self.bot.core.settings.discord.default_prefixes])

    @group(aliases=["customprefix"])
    @guild_only()
    @has_guild_permissions(manage_guild=True)
    @bot_has_permissions(embed_links=True)
    async def prefix(self, ctx) -> None:
        """
        Add/remove custom prefixes for this guild.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes",
                    description=dedent("""
                        No subcommand was input, or that subcommand was not found.

                        **Subcommand List:**
                        ``prefix add (prefix)`` - Add a custom prefix (up to 4).
                        ``prefix remove (prefix)`` - Remove a custom prefix.
                        ``prefix set (prefix)`` - Overrides all other prefixes.
                        ``prefix reset`` - Switch back to using the bot's default prefixes.
                    """.strip()),

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @prefix.group(name="set")
    async def prefix_set(self, ctx, prefix: str) -> None:
        """
        Overide all other custom prefixes and set one.
        """
        prefix = prefix.lower()
        if not is_valid_prefix(prefix):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Invalid Prefix",
                    description=self.invalid_prefix_description,
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            result.prefixes = [prefix]
        else:
            self.bot.db_session.add(
                CustomPrefixes(
                    guild_id=ctx.guild.id,
                    prefixes=[prefix],
                )
            )
        self.bot.db_session.commit()
        del self.bot.prefix_cache[ctx.guild.id]

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Custom Prefixes · Set",
                description=dedent(f"""
                    Succesfully replaced any other custom prefixes and set that one.

                    The bot will now respond to ``{prefix}`` on this guild.

                    ```Example Usage:\n{prefix}help```

                    The bot will still respond to mentions of its name, for example:
                    {self.bot.user.mention} help

                    You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                """.strip()),

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @prefix.group(name="add")
    async def prefix_add(self, ctx, prefix: str) -> None:
        """
        Add a custom prefix to this guild.
        """
        prefix = prefix.lower()
        if not is_valid_prefix(prefix):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Invalid Prefix",
                    description=self.invalid_prefix_description,
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            prefixes = list(result.prefixes)
            if len(prefixes) == 4:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Prefix Limit",
                        description="This guild has hit the 4 custom prefixes limit.\n\nYou can remove prefixes in order to add more.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

            if any([prefix.startswith(existing_prefix) for existing_prefix in prefixes]):
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Conflict",
                        description="This prefix would conflict with another prefix as this prefix starts with the other prefix.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return

            if prefix not in prefixes:
                prefixes.append(prefix)
                result.prefixes = prefixes
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Add",
                        description=dedent(f"""
                            **Succesfully added a custom prefix.**

                            The bot will now respond to ``{prefix}`` on this guild.

                            ```Example Usage:\n{prefix}help```

                            You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                        """.strip()),

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
            else:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Add",
                        description="That custom prefix is already added on this guild.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return
        else:
            self.bot.db_session.add(
                CustomPrefixes(
                    guild_id=ctx.guild.id,
                    prefixes=[prefix],
                )
            )

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Set",
                    description=dedent(f"""
                        **Succesfully set a new custom prefix.**

                        The bot will now only respond to ``{prefix}`` and mentions on this guild.

                        ```Example Usage:\n{prefix}help```

                        You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                    """),

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
        self.bot.db_session.commit()
        del self.bot.prefix_cache[ctx.guild.id]

    @prefix.group(name="remove", aliases=["rem", "delete"])
    async def prefix_remove(self, ctx, prefix: str) -> None:
        """
        Remove a custom prefix from this guild.
        """
        prefix = prefix.lower()
        if not is_valid_prefix(prefix):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Invalid Prefix",
                    description=self.invalid_prefix_description,
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )
            return

        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            prefixes = list(result.prefixes)

            if prefix in prefixes:
                other_info = ""

                if len(prefixes) > 1:
                    prefixes.remove(prefix)
                    result.prefixes = prefixes
                else:
                    other_info = f"\n\nAll custom prefixes have been removed. Defaulting to: {self.format_default_prefixes()}"
                    self.bot.db_session.delete(result)

                self.bot.db_session.commit()
                del self.bot.prefix_cache[ctx.guild.id]

                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Remove",
                        description=dedent(f"""
                            **Succesfully removed the prefix ``{prefix}``.**{other_info}

                            You can find the list of prefixes that the bot will respond to on this guild by mentioning the bot.
                        """.strip()),

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
            else:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Custom Prefixes · Remove",
                        description="That prefix is not a responding prefix on this guild.",
                        colour=0x8B0000,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    )
                )
                return
        else:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes · Remove",
                    description="There are no custom prefixes set up for this guild.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )

    @prefix.group(name="reset", aliases=["default"])
    async def prefix_reset(self, ctx) -> None:
        result = self.bot.db_session.query(CustomPrefixes).filter_by(guild_id=ctx.guild.id).first()
        if result is not None:
            self.bot.db_session.delete(result)
            self.bot.db_session.commit()
            del self.bot.prefix_cache[ctx.guild.id]

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Custom Prefixes",
                    description="Succesfully reset to the default prefixes.",
                    fields={
                        "Default Prefixes": self.format_default_prefixes(),
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
                    title="Custom Prefixes · Reset to Default",
                    description="There are no custom prefixes set up for this guild.",
                    colour=0x8B0000,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                )
            )


def setup(bot) -> None:
    bot.add_cog(Management(bot))
