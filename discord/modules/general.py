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
from discord.ext.commands import Cog, bot_has_permissions, command

from psutil import cpu_percent, virtual_memory

from discord.helpers.generators import RPANEmbed


class General(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.core_developers = [
            "[u/OneUpPotato](https://reddit.com/u/OneUpPotato)",
            "[u/JayRy27](https://reddit.com/u/JayRy27)",
            "[u/bsoyka](https://reddit.com/u/bsoyka)",
        ]

    @command(aliases=["information", "stats", "statistics"])
    @bot_has_permissions(embed_links=True)
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
                    "Core Developers": "\n".join(self.core_developers),
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
    @bot_has_permissions(embed_links=True)
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

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            )
        )

    @command(aliases=["contributors", "devs", "developers", "owners"])
    @bot_has_permissions(embed_links=True)
    async def credits(self, ctx) -> None:
        """
        View the list of people who have contributed to the bot.
        """
        other_contributors = [
            "Snoo Avatar: [u/doradiamond](https://reddit.com/u/doradiamond)",
        ]

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="RPANBot Contributors",
                description="This is a list of the people who have helped develop RPANBot.\nYou can also help contribute to the bot on [GitHub.](https://github.com/RPANBot/RPANBot)",
                fields={
                    "Core Developers": "\n".join(self.core_developers),
                    "Other Contributors": "\n".join(other_contributors),
                },

                url="https://github.com/RPANBot/RPANBot",
                thumbnail=self.bot.core.settings.links.bot_avatar,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @command()
    @bot_has_permissions(embed_links=True)
    async def invite(self, ctx) -> None:
        """
        Get a link to invite RPANBot to your guild.
        """
        invite_link = "https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={invite_permissions}".format(
            client_id=self.bot.core.settings.discord.client_id,
            invite_permissions=self.bot.core.settings.discord.invite_permissions,
        )

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Click here to invite the bot to your server.",
                description=f"You can also join the [bot support server!]({self.bot.core.settings.links.support_guild})",
                url=invite_link,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @command(aliases=["dashboard"])
    @bot_has_permissions(embed_links=True)
    async def website(self, ctx) -> None:
        """
        Get a link to the bot's website.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Click here to view the RPANBot web dashboard.",
                url="https://rpanbot.botcavern.xyz",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @command()
    @bot_has_permissions(embed_links=True)
    async def support(self, ctx) -> None:
        """
        Get a link to the bot's support Discord guild.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Click here to join the bot support server.",
                url=self.bot.core.settings.links.support_guild,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @command()
    @bot_has_permissions(embed_links=True)
    async def privacy(self, ctx) -> None:
        """
        Get a link to the bot's privacy policy.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Click here to view RPANBot's privacy policy.",
                url="https://rpanbot.botcavern.xyz/privacy",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @command(aliases=["feedback"])
    @bot_has_permissions(embed_links=True)
    async def contact(self, ctx, *, note: str) -> None:
        """
        Contact or send feedback to the bot's developers.
        """
        contact_channel = await self.bot.find_channel(self.bot.core.settings.ids.contact_channel)

        await contact_channel.send(
            "",
            embed=RPANEmbed(
                title="New Message!",
                fields={
                    "Note": note,
                    "User": f"{ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})",
                    "Guild": f"{ctx.guild.name} ({ctx.guild.id})",
                },
                thumbnail=ctx.author.avatar_url,
            ),
        )

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Message Sent!",
                description="Thanks for reaching out to the bot's developers!",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )


def setup(bot) -> None:
    bot.add_cog(General(bot))
