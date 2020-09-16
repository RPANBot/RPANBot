# General Module
from discord.ext import commands

from textwrap import dedent

from psutil import cpu_percent, virtual_memory

from utils.helpers import generate_embed

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["cpu", "memory"])
    async def info(self, ctx):
        """
        Get some information about the bot.
        """
        await ctx.send(
            "",
            embed=generate_embed(
                title="Information",
                description="You can see a list of commands by using '{prefix}help'.".format(prefix=self.bot.get_relevant_prefix(ctx.message)),
                fields={
                    "Core Developers": "OneUpPotato#1418\nJayRy27#0001\nbsoyka#0001",
                    "Joined Servers": len(self.bot.guilds),
                    "Unique Members": len(set(self.bot.get_all_members())),
                    "Ping": f"{round(self.bot.latency * 1000)}ms",
                    "CPU/Memory Usage": f"{cpu_percent()}%/{virtual_memory().percent}%",
                    "Lines of Code": f"{self.bot.lines_of_code}",
                },
                thumbnail=self.bot.bot_avatar_link,
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @commands.command(aliases=["latency"])
    async def ping(self, ctx):
        """
        View the current latency of the bot.
        """
        await ctx.send(
            "",
            embed=generate_embed(
                title="Pong!",
                description=f"{round(self.bot.latency * 1000)}ms",
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @commands.command(aliases=["developers","owner"])
    async def contributors(self, ctx):
        """
        Get a list of the bot's contributors.
        """
        core_developers = [
            "[u/OneUpPotato](https://reddit.com/user/OneUpPotato)",
            "[u/bsoyka](https://reddit.com/user/bsoyka)",
            "[u/JayRy27](https://reddit.com/user/JayRy27)",
        ]

        other_contributors = [
            "Snoo Avatar: [u/doradiamond](https://reddit.com/user/doradiamond)",
        ]

        await ctx.send(
            "",
            embed=generate_embed(
                title="Contributors",
                description="This is a list of the people who have helped develop RPANBot.\nYou can also help contribute to the bot on [GitHub.](https://github.com/RPANBot/RPANBot)",
                fields={
                    "Core Developers": "\n".join(core_developers),
                    "Other Contributors": "\n".join(other_contributors),
                },
                footer_text="None",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @commands.command()
    async def invite(self, ctx):
        """
        Get an invite link for the bot.
        """
        await ctx.send(
            "",
            embed=generate_embed(
                title="Click here to invite the bot to your server.",
                description=f"You can also join the [bot support server!]({self.bot.support_guild_link})",
                url=f"{self.bot.bot_invite_link}",
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @commands.command()
    async def support(self, ctx):
        """
        Get an invite link for the bot's support server.
        """
        await ctx.send(
            "",
            embed=generate_embed(
                title="Click here to join the bot support server.",
                url=self.bot.support_guild_link,
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @commands.command()
    async def privacy(self, ctx):
        """
        View information on what data RPANBot collects.
        """
        await ctx.send(
            "",
            embed=generate_embed(
                title="Privacy Policy",
                description=dedent("""
                    RPANBot only stores information when it is needed to provide one of its features. The bot only stores stream notification settings and custom guild prefixes, which are both provided to it by you setting up those particular features.

                    You can contact the developers using the bot's feedback command requesting that any settings for your guild be deleted, or you can delete your stream notifications settings using a command and set the custom prefix back to the bot's default prefix.

                    When the bot leaves/is removed from a guild, it'll attempt to delete any settings it has stored for it.
                """).strip(),
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @commands.command()
    async def feedback(self, ctx, *, feedback: str):
        """
        Send feedback to the bot's developers.
        """
        feedback_channel = await self.bot.fetch_channel(727205462377758810)

        user = ctx.author
        await feedback_channel.send(
            "",
            embed=generate_embed(
                title="New Feedback!",
                thumbnail=ctx.author.avatar_url,
                fields={
                    "Feedback": feedback,
                    "User": f"{user.name}#{user.discriminator} ({user.id})",
                    "Guild": f"{ctx.guild.name} ({ctx.guild.id})",
                },
                footer_text="None",
                bot=self.bot,
                message=ctx.message
            ),
        )

        await ctx.send(
            "",
            embed=generate_embed(
                title="Feedback Sent!", description="Thanks for your help!",
                bot=self.bot, message=ctx.message
            ),
        )

def setup(bot):
    bot.add_cog(General(bot))
