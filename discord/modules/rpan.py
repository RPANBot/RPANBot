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
from discord.ext.commands import Cog, bot_has_permissions, command, check

from typing import Optional
from textwrap import dedent

from discord.helpers.utils import parse_link
from discord.helpers.checks import is_rpan_guild
from discord.helpers.generators import RPANEmbed


class RPAN(Cog):
    """
    This cog contains all the RPAN related commands.
    """
    def __init__(self, bot) -> None:
        self.bot = bot

    @command()
    @bot_has_permissions(embed_links=True)
    async def wiki(self, ctx) -> None:
        """
        Get a link to the r/pan wiki.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Click here to view the RPAN wiki.",
                url="https://www.reddit.com/r/pan/wiki/index",

                user=ctx.author,
                bot=self.bot,
                message=ctx.message
            ),
        )

    @command(aliases=["howtostream"])
    @bot_has_permissions(embed_links=True)
    async def howtobroadcast(self, ctx) -> None:
        """
        Get information on how to broadcast to RPAN.
        """
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Click here to view the section on the RPAN wiki.",
                url="https://www.reddit.com/r/pan/wiki/index#wiki_how_do_i_broadcast_on_mobile.3F",
                description=dedent("""
                    There are two ways to broadcast to RPAN: from mobile and from desktop.

                    You can easily broadcast from mobile using the [Reddit app.](https://www.reddit.com/r/pan/wiki/index#wiki_how_do_i_broadcast_on_mobile.3F)

                    To broadcast from desktop, you can use [RPAN Studio.](https://www.reddit.com/r/RPANStudio/comments/hjimlq/you_want_a_desktop_streaming_solution_you_got_it/)
                """).strip(),

                user=ctx.author,
                bot=self.bot,
                message=ctx.message
            ),
        )

    @command(aliases=["ts", "topbroadcast", "tb"])
    @bot_has_permissions(embed_links=True)
    async def topstream(self, ctx, subreddit: Optional[str] = None) -> None:
        """
        Get the current top RPAN broadcast.
        """
        if subreddit is not None:
            subreddit = self.bot.core.rpan_subreddits.ref_to_full(subreddit)

        broadcasts = self.bot.core.strapi.get_broadcasts()
        if broadcasts is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Top Broadcast",
                    description="There was a problem with fetching the top broadcasts, please try again later.",
                    colour=0xD2D219,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            return

        top_broadcast = broadcasts.top_broadcast(subreddit=subreddit)
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Current Top Broadcast{}".format("" if subreddit is None else f" (on r/{subreddit})"),
                fields={
                    "Title": top_broadcast.title,
                    "Author": f"u/{top_broadcast.author_name}",
                    "Subreddit": f"r/{top_broadcast.subreddit_name}",
                    "RPAN Rank": f"{top_broadcast.global_rank}/{top_broadcast.total_streams}",
                    "Current Viewers": top_broadcast.continuous_watchers,
                    "Unique Viewers": top_broadcast.unique_watchers,
                },

                url=top_broadcast.url,
                thumbnail=top_broadcast.thumbnail,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message
            ),
        )

    @command(aliases=["stream", "s", "broadcast", "b", "broadcaststats"])
    @bot_has_permissions(embed_links=True)
    async def streamstats(self, ctx, *, stream: parse_link) -> None:
        """
        Get the statistics of a given RPAN broadcast.
        """
        broadcast = self.bot.core.strapi.get_broadcast(stream)
        if broadcast is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Broadcast Statistics",
                    description="There was a problem finding that broadcast.",
                    colour=0xD2D219,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            return

        fields = {
            "Title": broadcast.title,
            "Author": f"u/{broadcast.author_name}",
            "Subreddit": f"r/{broadcast.subreddit_name}",
            "Status": ("Live" if broadcast.is_live else "Off Air"),
        }

        if broadcast.is_live:
            fields["Current Viewers"] = str(broadcast.continuous_watchers)
        else:
            fields["Broadcasted"] = self.bot.core.strapi.format_broadcast_timestamp(broadcast.published_at).strftime("%d/%m/%Y at %H:%M UTC")

        fields["Unique Viewers"] = str(broadcast.unique_watchers)

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Broadcast Statistics",
                fields=fields,

                url=broadcast.url,
                thumbnail=broadcast.thumbnail,

                user=ctx.author,
                bot=self.bot,
                message=ctx.message
            ),
        )

    @command(aliases=["viewbroadcast", "laststream", "broadcaster", "streamer"])
    @bot_has_permissions(embed_links=True)
    async def viewstream(self, ctx, username: str) -> None:
        """
        Get the current or last stream of a specified user.
        """
        broadcasts = self.bot.core.strapi.get_broadcasts()
        if broadcasts is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="View Stream",
                    description="There was a problem with fetching the broadcasts, please try again later.",
                    colour=0xD2D219,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            return

        broadcast = broadcasts.has_streamer(name=username)
        if broadcast:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title=f"u/{broadcast.author_name}'s Current Broadcast (Live)",
                    fields={
                        "Title": broadcast.title,
                        "Author": f"u/{broadcast.author_name}",
                        "Subreddit": f"r/{broadcast.subreddit_name}",
                        "RPAN Rank": f"{broadcast.global_rank}/{broadcast.total_streams}",
                        "Current Viewers": broadcast.continuous_watchers,
                        "Unique Viewers": broadcast.unique_watchers,
                    },

                    url=broadcast.url,
                    thumbnail=broadcast.thumbnail,

                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            broadcast = self.bot.core.strapi.get_last_broadcast(username)
            if broadcast:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title=f"u/{broadcast.author_name}'s Last Broadcast",
                        fields={
                            "Title": broadcast.title,
                            "Author": f"u/{broadcast.author_name}",
                            "Subreddit": f"r/{broadcast.subreddit_name}",
                            "Status": "Off-Air",
                            "Broadcasted": self.bot.core.strapi.format_broadcast_timestamp(broadcast.published_at).strftime("%d/%m/%Y at %H:%M UTC"),
                            "Unique Viewers": broadcast.unique_watchers,
                        },

                        url=broadcast.url,
                        thumbnail=broadcast.thumbnail,

                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    ),
                )
            else:
                await ctx.send("No last broadcast was found for that user.")

    @command(aliases=["topbroadcasts"])
    @bot_has_permissions(embed_links=True)
    async def topstreams(self, ctx, time_period: Optional[str] = None) -> None:
        """
        View the top broadcasts on each RPAN subreddit.
        """
        top_broadcasts, time = self.bot.core.strapi.get_top_broadcasts(time_period)

        fields = {}
        for subreddit, broadcast in top_broadcasts.items():
            if broadcast is not None:
                fields[f"r/{subreddit}"] = f"[{broadcast.title}]({broadcast.url})"

        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Top Broadcasts",
                description=f"The top broadcast on each RPAN subreddit from within: {time}.",
                fields=fields,

                user=ctx.author,
            )
        )

    @command(aliases=["abuse"])
    @check(is_rpan_guild)
    @bot_has_permissions(embed_links=True)
    async def report(self, ctx, *, type: str = None) -> None:
        """
        Get information on how to report policy breaking content.
        """
        if type is not None:
            type = type.lower()

        report_tables = {
            "promoting hate based on identity or vulnerability": "https://www.reddit.com/report?reason=its-promoting-hate-based-on-identity-or-vulnerability",
            "spam": "https://www.reddit.com/report?reason=this-is-spam",
            "misinformation": "https://www.reddit.com/report?reason=this-is-misinformation",
            "targeted harassment": "https://www.reddit.com/report?reason=its-targeted-harassment",
            "violence or physical harm": "https://www.reddit.com/report?reason=it-threatens-violence-or-physical-harm",
            "rude, vulgar, or offensive": "https://www.reddit.com/report?reason=its-rude-vulgar-or-offensive",
            "abusing the report button": "https://www.reddit.com/report?reason=its-abusing-the-report-button",
            "copyright infringements": "https://www.reddit.com/report?reason=it-infringes-my-copyright",
            "trademark infringement": "https://www.reddit.com/report?reason=it-infringes-my-trademark-rights",
            "personal information": "https://www.reddit.com/report?reason=its-personal-and-confidential-information",
            "sexualizing minors": "https://www.reddit.com/report?reason=its-sexual-or-suggestive-content-involving-minors",
            "involuntary pornography": "https://www.reddit.com/report?reason=its-involuntary-pornography",
            "ban evasion": "https://www.reddit.com/report?reason=its-ban-evasion",
            "vote manipulation": "https://www.reddit.com/report?reason=its-vote-manipulation",
            "prohibited goods or services": "https://www.reddit.com/report?reason=its-a-transaction-for-prohibited-goods-or-services",
            "impersonation": "https://www.reddit.com/report?reason=it-impersonates-me",
            "netzdg report": "https://www.reddit.com/report?reason=report-this-content-under-netzdg",
            "self-harm or suicide": "https://www.reddit.com/report?reason=someone-is-considering-suicide-or-serious-self-harm",
            "appeal a suspension": "https://www.reddit.com/appeals",
            "appeal a subreddit ban": "https://www.reddit.com/message/compose?to=/r/reddit.com&subject=Subreddit+Ban+Appeal",
            "dmca": "https://www.redditinc.com/policies/user-agreement#text-content8",
        }

        if type is not None and type not in report_tables.keys():
            aliases = {
                "rude": "rude, vulgar, or offensive",
                "vulgar": "rude, vulgar, or offensive",
                "offensive": "rude, vulgar, or offensive",
                "copyright infringement": "copyright infringements",
                "copyright": "copyright infringements",
                "trademark": "trademark infringement",
                "dox": "personal information",
                "harassment": "targeted harassment",
                "discrimination": "promoting hate based on identity or vulnerability",
                "racism": "promoting hate based on identity or vulnerability",
                "hate": "promoting hate based on identity or vulnerability",
                "self-harm": "self-harm or suicide",
                "netzdg": "netzdg report",
                "violence": "violence or physical harm",
                "harm": "violence or physical harm",
            }

            if type in aliases.keys():
                type = aliases[type]

        embed = RPANEmbed(
            title="Click here to go to the report page.",
            description=dedent("""
                If you need to report a user, comment, or post, please go to https://reddit.com/report (or click above) and report the content there.

                If you cannot find a category for the content you want to report, then [send a message to r/reddit.com](https://reddit.com/message/compose/?to=/r/reddit.com) with the content.
            """.strip()),
            url="https://reddit.com/report",

            user=ctx.author,
        )

        if type in report_tables.keys():
            embed.url = report_tables[type]
            embed.description = dedent("""
                Visit the following link (or click above) to report for '{type}':
                {link}
            """.strip()).format(type=type.capitalize(), link=embed.url)

        await ctx.send("", embed=embed)


def setup(bot) -> None:
    bot.add_cog(RPAN(bot))
