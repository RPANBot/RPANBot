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
from discord.ext.commands import Cog, command

from psutil import cpu_percent, virtual_memory

from discord.helpers.generators import RPANEmbed


class General(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @command(aliases=["information", "stats", "statistics"])
    async def info(self, ctx) -> None:
        """
        Get some statistics about the bot.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="RPANBot Information",
                description="RPANBot is the bot that connects the Reddit Public Access Network and Discord together.\n\nThe bot has many features, such as stream stats, getting when a user last streamed, getting the current top broadcast, and notifications for when someone goes live.",
                fields={
                    "Core Developers": "[u/OneUpPotato](https://reddit.com/u/OneUpPotato)\n[u/JayRy27](https://reddit.com/u/JayRy27)\n[u/bsoyka](https://reddit.com/u/bsoyka)",
                    "Joined Guilds": len(self.bot.guilds),
                    "Total Users": self.bot.user_count,

                    "Ping": f"{round(self.bot.latency * 1000)}ms",
                    "CPU/Memory Usage": f"{cpu_percent()}%/{virtual_memory().percent}%",
                    "Lines of Code": self.bot.core.lines_of_code,
                },

                url="https://rpanbot.botcavern.xyz/",
                thumbnail=self.bot.core.settings.links.bot_avatar,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @command(aliases=["latency"])
    async def ping(self, ctx) -> None:
        """
        View the current latency of the bot.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Pong!",
                description=f"{round(self.bot.latency * 1000)}ms",

                url="https://rpanbot.botcavern.xyz/",
                thumbnail=self.bot.core.settings.links.bot_avatar,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @command(aliases=["devs", "developers", "owners"])
    async def contributors(self, ctx) -> None:
        """
        View the list of people who have contributed to the bot.
        """
        core_developers = [
            "[u/OneUpPotato](https://reddit.com/u/OneUpPotato)",
            "[u/bsoyka](https://reddit.com/u/bsoyka)",
            "[u/JayRy27](https://reddit.com/u/JayRy27)",
        ]

        other_contributors = [
            "Snoo Avatar: [u/doradiamond](https://reddit.com/u/doradiamond)",
        ]

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="RPANBot Contributors",
                description="This is a list of the people who have helped develop RPANBot.\nYou can also help contribute to the bot on [GitHub.](https://github.com/RPANBot/RPANBot)",
                fields={
                    "Core Developers": "\n".join(core_developers),
                    "Other Contributors": "\n".join(other_contributors),
                },

                url="https://github.com/RPANBot/RPANBot",
                thumbnail=self.bot.core.settings.links.bot_avatar,

                bot=self.bot,
                message=ctx.message,
            ),
        )


def setup(bot) -> None:
    bot.add_cog(General(bot))
