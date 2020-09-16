from discord import Color, Embed, Message, TextChannel
from discord.ext import commands

import asyncio
from re import search
from base36 import dumps, loads

from utils.helpers import generate_embed, is_main_dev, is_rpan_bot_guild
from utils.settings import get_approved_bugs_channel, get_bug_reports_channel, get_denied_bugs_channel

def author_channel_check(author, channel):
    def inner_check(message):
        return message.author == author and message.channel == channel

    return inner_check

class SupportServer(commands.Cog, name="RPANBot Support Server"):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    @commands.check(is_rpan_bot_guild)
    async def bug(self, ctx):
        """
        Commands related to bug tracking.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Tracking",
                    description="You are authorised to use this command, but input an invalid subcommand.",
                    footer_text="None",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @bug.group(pass_context=True, name="report", aliases=["new"])
    @commands.cooldown(1, 120)
    async def bug_report(self, ctx):
        """
        Report a bug
        """
        try:
            desc_ask = await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Report - Step 1/4",
                    fields={
                        "Answer with": "A short description, around one sentence",
                        "Respond within": "30 seconds",
                    },
                ),
            )
            description = await self.bot.wait_for(
                "message",
                check=author_channel_check(ctx.author, ctx.channel),
                timeout=30,
            )

            repro_ask = await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Report - Step 2/4",
                    fields={
                        "Answer with": "The steps to reproduce the bug",
                        "Respond within": "120 seconds",
                    },
                ),
            )
            reproduction = await self.bot.wait_for(
                "message",
                check=author_channel_check(ctx.author, ctx.channel),
                timeout=120,
            )

            exp_ask = await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Report - Step 3/4",
                    fields={
                        "Answer with": "The expected result",
                        "Respond within": "60 seconds",
                    },
                ),
            )
            expected = await self.bot.wait_for(
                "message",
                check=author_channel_check(ctx.author, ctx.channel),
                timeout=60,
            )

            act_ask = await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Report - Step 3/4",
                    fields={
                        "Answer with": "The actual result",
                        "Respond within": "60 seconds",
                    },
                ),
            )
            actual = await self.bot.wait_for(
                "message",
                check=author_channel_check(ctx.author, ctx.channel),
                timeout=60,
            )
        except asyncio.TimeoutError:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Report - Error",
                    description="This command timed out.",
                    color=Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            return

        channel = await self.bot.fetch_channel(get_bug_reports_channel())

        embed = Embed(
            title="Bug Report - New",
            description=description.content,
            color=Color(0x00688B),
        )
        embed.set_author(name=str(ctx.author), icon_url=str(ctx.author.avatar_url))

        embed.add_field(
            name="Steps to reproduce", value=reproduction.content, inline=False
        )
        embed.add_field(name="Expected result", value=expected.content, inline=True)
        embed.add_field(name="Actual result", value=actual.content, inline=True)

        msg = await channel.send("", embed=embed)

        report_id = dumps(msg.id)
        embed.set_author(
            name=f"{ctx.author} · {report_id}", icon_url=str(ctx.author.avatar_url)
        )
        await msg.edit(embed=embed)

        confirmation = await ctx.send(
            "",
            embed=generate_embed(
                title="Bug Report - Success",
                description=f"Your bug report has been placed in {channel.mention} for approval/denial.",
            ),
        )

        await asyncio.sleep(7)

        for message in (
            ctx.message,
            desc_ask,
            description,
            repro_ask,
            reproduction,
            exp_ask,
            expected,
            act_ask,
            actual,
            confirmation,
        ):
            await message.delete()

    @bug_report.error
    async def bug_report_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Report - Error",
                    description="This command is limited to certain Discord servers.",
                    color=Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        elif isinstance(error, commands.errors.CommandOnCooldown):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Bug Report - Error",
                    description="This command is currently on cooldown to prevent spam and ratelimiting.\n%.2fs remaining."
                    % error.retry_after,
                    color=Color(0x8B0000),
                    footer_text="Requested by {}".format(str(ctx.author)),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            pass
        else:
            raise error

    @bug.group(pass_context=True, name="approve")
    @commands.check(is_main_dev)
    async def bug_approve(self, ctx, report_id: str, *, reason: str = "Not specified"):
        """
        Approve a bug report
        """
        report_message_id = loads(report_id)
        channel = await self.bot.fetch_channel(get_bug_reports_channel())
        report_message = await channel.fetch_message(report_message_id)

        embed = report_message.embeds[0]
        embed.title = "Bug Report - Approved"
        embed.color = Color(0x006E0F)

        embed.set_footer(text=f"Reason: {reason}")

        pattern = r"(.+#\d{4}) · [a-z0-9]+"
        result = search(pattern, embed.author.name)
        embed.set_author(name=result.group(1), icon_url=embed.author.icon_url)

        await report_message.delete()
        approved_channel = await self.bot.fetch_channel(get_approved_bugs_channel())
        await approved_channel.send("", embed=embed)

        confirmation_message = await ctx.send(
            f"You've approved the report with ID: {report_id}"
        )

        await asyncio.sleep(5)
        await ctx.message.delete()
        await confirmation_message.delete()

    @bug.group(pass_context=True, name="deny")
    @commands.check(is_main_dev)
    async def bug_deny(self, ctx, report_id: str, *, reason: str):
        """
        Deny a bug report
        """
        report_message_id = loads(report_id)
        channel = await self.bot.fetch_channel(get_bug_reports_channel())
        report_message = await channel.fetch_message(report_message_id)

        embed = report_message.embeds[0]
        embed.title = "Bug Report - Denied"
        embed.color = Color(0x8B0000)

        embed.set_footer(text=f"Reason: {reason}")

        pattern = r"(.+#\d{4}) · [a-z0-9]+"
        result = search(pattern, embed.author.name)
        embed.set_author(name=result.group(1), icon_url=embed.author.icon_url)

        await report_message.delete()
        denied_channel = await self.bot.fetch_channel(get_denied_bugs_channel())
        await denied_channel.send("", embed=embed)

        confirmation_message = await ctx.send(
            f"You've denied the report with ID: {report_id}"
        )

        await asyncio.sleep(5)
        await ctx.message.delete()
        await confirmation_message.delete()

def setup(bot):
    bot.add_cog(SupportServer(bot))
