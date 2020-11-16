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
from discord import DMChannel
from discord.ext.commands import Cog, DefaultHelpCommand, HelpCommand

from textwrap import dedent
from itertools import groupby

from discord.helpers.generators import RPANEmbed


class RPANBotHelpCommand(HelpCommand):
    def wrap_listing(self, listing: str) -> str:
        return "```md\n" + listing.strip() + "\n```"

    async def send_bot_help(self, mapping) -> None:
        help_embed = RPANEmbed(
            title="RPANBot Command List",
            description=dedent(f"""
                **Info**
                Type ``{self.clean_prefix}help (command name)`` for more info on a command.
                [Click here to view a more in-depth description of the commands.](https://rpanbot.botcavern.xyz/commands)

                **Argument Key**
                [argument] | optional argument
                <argument> | required argument
            """.strip()),

            url="https://rpanbot.botcavern.xyz/commands",

            user=self.context.author,
            bot=self.context.bot,
            message=self.context.message,
        )

        def get_category(command):
            cog = command.cog
            return cog.qualified_name if cog is not None else "None"

        filtered = await self.filter_commands(self.context.bot.commands, sort=True, key=get_category)

        category_fields = {}
        for category, commands in groupby(filtered, key=get_category):
            if category == "None":
                continue

            commands = sorted(commands, key=lambda cmd: len(cmd.name))

            category_cmds = ""
            for cmd in commands:
                cmd_line = "\n\n" + cmd.name

                if cmd.signature:
                    cmd_line += " " + cmd.signature

                if cmd.help:
                    cmd_line += ":\n  · " + cmd.help

                category_cmds += cmd_line

            category_fields[category] = self.wrap_listing(category_cmds)

        category_fields = sorted(category_fields.items(), key=lambda cat: len(cat[1]), reverse=True)
        for category_info in category_fields:
            help_embed.add_field(
                name=category_info[0],
                value=category_info[1],
                inline=False,
            )

        await self.send_help_message(
            channel=self.get_destination(),
            text="",
            embed=help_embed,
        )

    async def send_cog_help(self, cog) -> None:
        cog_help_embed = RPANEmbed(
            title="RPANBot Help · " + cog.qualified_name,
            description="Something went wrong.",

            url="https://rpanbot.botcavern.xyz/commands",

            user=self.context.author,
            bot=self.context.bot,
            message=self.context.message,
        )

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        if filtered:
            description = dedent(f"""
                **Info**
                Type ``{self.clean_prefix}help (command name)`` for more info on a command.
                [Click here to view a more in-depth description of the commands.](https://rpanbot.botcavern.xyz/commands)

                **Argument Key**
                [argument] | optional argument
                <argument> | required argument
            """.strip())

            listing = ""
            for cmd in filtered:
                cmd_line = "\n\n" + cmd.name

                if cmd.signature:
                    cmd_line += " " + cmd.signature

                if cmd.help:
                    cmd_line += ":\n  · " + cmd.help

                listing += cmd_line
            listing = self.wrap_listing(listing)

            description += f"\n\n**Commands:**\n{listing}"

            cog_help_embed.description = description
        else:
            cog_help_embed.description = f"There are currently no commands for {cog.qualified_name}."

        await self.send_help_message(
            channel=self.get_destination(),
            text="",
            embed=cog_help_embed,
        )

    async def send_group_help(self, group) -> None:
        group_help_embed = RPANEmbed(
            title="RPANBot Subcommands Help · " + group.qualified_name,
            description="Something went wrong.",

            url="https://rpanbot.botcavern.xyz/commands",

            user=self.context.author,
            bot=self.context.bot,
            message=self.context.message,
        )

        filtered = await self.filter_commands(group.commands, sort=True)
        if filtered:
            description = dedent(f"""
                {group.description}

                **Info**
                Type ``{self.clean_prefix}{group.name} (command)`` to use a command listed here.
                [Click here to view a more in-depth description of the commands.](https://rpanbot.botcavern.xyz/commands)

                **Argument Key**
                [argument] | optional argument
                <argument> | required argument
            """.strip())

            listing = ""
            for cmd in filtered:
                cmd_line = "\n\n" + cmd.name

                if cmd.signature:
                    cmd_line += " " + cmd.signature

                if cmd.help:
                    cmd_line += ":\n  · " + cmd.help

                listing += cmd_line
            listing = self.wrap_listing(listing)

            description += f"\n\n**Commands:**\n{listing}"

            group_help_embed.description = description
        else:
            group_help_embed.description = f"There are currently no commands for {group.qualified_name}."

        await self.send_help_message(
            channel=self.get_destination(),
            text="",
            embed=group_help_embed,
        )

    async def send_command_help(self, cmd) -> None:
        cmd_help_embed = RPANEmbed(
            title="RPANBot Command Help",
            description="Something went wrong.",

            url="https://rpanbot.botcavern.xyz/commands",

            user=self.context.author,
            bot=self.context.bot,
            message=self.context.message,
        )

        cmd_description = f"**Usage:** ``{self.clean_prefix}{cmd.name} {cmd.signature}``"

        if cmd.aliases:
            aliases = ", ".join([f"``{alias}``" for alias in cmd.aliases])
            cmd_description += f"\n\n**Also usable as:**\n{aliases}"

        if cmd.help:
            cmd_description += f"\n\n**Description:**\n``{cmd.help}``"

        cmd_help_embed.description = cmd_description

        await self.send_help_message(
            channel=self.get_destination(),
            text="",
            embed=cmd_help_embed,
        )

    async def send_help_message(self, channel, text: str, embed: RPANEmbed) -> None:
        if not isinstance(channel, DMChannel):
            if not channel.guild.me.guild_permissions.embed_links:
                await channel.send("RPANBot requires the 'Embed Links' permission for most of its commands (including the help menu).")
                return

        await channel.send(
            content=text,
            embed=embed,
        )


class HelpCmd(Cog):
    """
    This cog handles the custom RPANBot help command.
    """
    def __init__(self, bot) -> None:
        self.bot = bot
        self.bot.help_command = RPANBotHelpCommand()


def setup(bot) -> None:
    bot.add_cog(HelpCmd(bot))


def teardown(bot) -> None:
    bot.help_command = DefaultHelpCommand()
