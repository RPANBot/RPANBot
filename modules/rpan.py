# Reddit Public Access Network Module
from datetime import datetime, timezone
from re import sub
from textwrap import dedent

import discord
from discord.ext import commands

from .utils.reddit import get_reddit
from .utils.settings import get_rpan_sub_abbreviations
from .utils.classes import Broadcast, Broadcasts, PushshiftBroadcasts
from .utils.helpers import generate_embed, is_rpan_guild

class RPAN(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wiki(self, ctx):
        """
        Get a link to the r/pan wiki.
        """
        await ctx.send(
            "",
            embed=generate_embed(
                title="Click here to view the RPAN wiki.",
                url="https://www.reddit.com/r/pan/wiki/index",
                footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @commands.command(aliases=["ts", "topbroadcast", "tb"])
    async def topstream(self, ctx, subreddit: str="all"):
        """
        Find the current top RPAN stream (optionally: on a specific subreddit)
        """
        sub_abbreviations = get_rpan_sub_abbreviations()
        if subreddit.lower() in sub_abbreviations.keys():
            subreddit = sub_abbreviations[subreddit.lower()]

        if subreddit.lower() == "all":
            subreddit = None

        broadcasts = Broadcasts()
        if broadcasts.api_status == "success":
            top_broadcast = broadcasts.get_top(subreddit)
            if top_broadcast != None:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Current Top Stream{}".format("" if subreddit == None else f" (on r/{subreddit.lower()})"),
                        url=top_broadcast.url,
                        fields={
                            "Title": top_broadcast.title,
                            "Author": f"u/{top_broadcast.author_name}",
                            "Subreddit": f"r/{top_broadcast.subreddit_name}",
                            "RPAN Rank": f"{top_broadcast.global_rank}/{top_broadcast.total_streams}",
                            "Current Viewers": f"{top_broadcast.continuous_watchers}",
                            f"Unique Viewers": f"{top_broadcast.unique_watchers}",
                        },
                        thumbnail=top_broadcast.thumbnail,
                        footer_text=f"Requested by {ctx.author}",
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
            else:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Top Stream",
                        description="Either there are no broadcasts on that subreddit right now, or that isn't an RPAN subreddit.",
                        color=discord.Color(0xD2D219),
                        footer_text=f"Requested by {ctx.author}",
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        else:
            await ctx.send(f"{ctx.author.mention} - There is a problem with getting RPAN broadcasts/that broadcast right now.")

    @commands.command(aliases=["ss", "broadcaststats", "bs", "stats", "streaminfo", "si", "broadcastinfo", "bi"])
    async def streamstats(self, ctx, stream):
        """
        Get the statistics of an RPAN broadcast.
        """

        stream_id = (
            sub("http(s)?://", "", stream)
            .replace("www.reddit.com/", "")
            .replace("old.reddit.com/", "")
            .replace("reddit.com/", "")
            .replace("redd.it/", "")
        )
        stream_id = sub("(rpan/r|r)/(.*?)/(comments/)?", "", stream_id).split("/")[0].split("?")[0]

        broadcast = Broadcast(id=stream_id, retry=True)
        if broadcast.api_status == "success":
            fields = {
                "Title": broadcast.title,
                "Author": f"u/{broadcast.author_name}",
                "Subreddit": f"r/{broadcast.subreddit_name}",
                "Status": ("Live" if broadcast.is_live else "Off Air"),
            }

            if broadcast.is_live:
                fields["Current Viewers"] = f"{broadcast.continuous_watchers}"
            else:
                # Get time in Coordinated Universal Time, then format it.
                fields["Broadcasted"] = datetime.fromtimestamp(int(broadcast.published_at / 1000), tz=timezone.utc).strftime("%d/%m/%Y at %H:%M UTC")

            fields["Unique Viewers"] = f"{broadcast.unique_watchers}"

            await ctx.send(
                "",
                embed=generate_embed(
                    title="Stream Statistics",
                    url=broadcast.url,
                    fields=fields,
                    thumbnail=broadcast.thumbnail,
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message
                ),
            )
        elif broadcast.api_status == "video not found":
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Stream Statistics",
                        description="No broadcast was found. Is that an RPAN broadcast? Is the URL/ID correct?",
                        color=discord.Color(0xD2D219),
                        footer_text=f"Requested by {ctx.author}",
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        else:
            await ctx.send(f"{ctx.author.mention} - There is a problem with getting RPAN broadcasts right now.")

    @commands.command(aliases=["vs","viewbroadcast","vb","laststream","getstream","gs","getbroadcast","gb"])
    async def viewstream(self, ctx, username):
        """
        Get the current stream/last stream of a user.
        """
        username = username.replace("/u/","").replace("u/","").lower()

        broadcasts = Broadcasts()
        if broadcasts.api_status == "success":
            found_broadcast = broadcasts.has_streamer(username)
            if found_broadcast != False:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title=f"u/{found_broadcast.author_name}'s Current Stream (Live)",
                        url=found_broadcast.url,
                        fields={
                            "Title": found_broadcast.title,
                            "Author": f"u/{found_broadcast.author_name}",
                            "Subreddit": f"r/{found_broadcast.subreddit_name}",
                            "RPAN Rank": f"{found_broadcast.global_rank}/{found_broadcast.total_streams}",
                            "Current Viewers": f"{found_broadcast.continuous_watchers}",
                            "Unique Viewers": f"{found_broadcast.unique_watchers}",
                        },
                        thumbnail=found_broadcast.thumbnail,
                        footer_text=f"Requested by {ctx.author}",
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
            else:
                last_broadcast = PushshiftBroadcasts(username).find_undeleted()
                if last_broadcast != None:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title=f"u/{last_broadcast.author_name}'s Last Stream (Off-Air)",
                            url=last_broadcast.url,
                            fields={
                                "Title": last_broadcast.title,
                                "Author": f"u/{last_broadcast.author_name}",
                                "Subreddit": f"r/{last_broadcast.subreddit_name}",
                                "Status": "Off-Air",
                                "Broadcasted": format_timestamp(last_broadcast.published_at),
                                "Unique Viewers": f"{last_broadcast.unique_watchers}",
                            },
                            thumbnail=last_broadcast.thumbnail,
                            footer_text=f"Requested by {ctx.author}",
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
                else:
                    await ctx.send(
                        "",
                        embed=generate_embed(
                            title="View Stream",
                            description="Unable to find that user's last broadcast.",
                            color=discord.Color(0xD2D219),
                            footer_text=f"Requested by {ctx.author}",
                            bot=self.bot,
                            message=ctx.message
                        ),
                    )
        else:
            await ctx.send(f"{ctx.author.mention} - There is a problem with getting RPAN broadcasts right now.")

    @commands.command(aliases=["abuse"])
    @commands.check(is_rpan_guild)
    async def report(self, ctx, *, type=None):
        """
        Get information on how to report policy breaking content.
        """
        if isinstance(type, str):
            type = type.lower()

        accepted_types = {
            "promoting hate based on identity or vulnerability": "https://www.reddit.com/report?reason=its-promoting-hate-based-on-identity-or-vulnerability",
            "spam": "https://www.reddit.com/report?reason=this-is-spam",
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

        if type != None and type not in accepted_types.keys():
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

        embed = generate_embed(
            title="Click here to go to the report page.",
            description="Did you find a user that is violating the Reddit Content Policy but don’t know how to report them? Just head on over to reddit.com/report (or click above) and you can report the user there.",
            url="https://reddit.com/report",
            footer_text=f"Requested by {ctx.author}",
            bot=self.bot,
            message=ctx.message
        )

        if type != None and type in accepted_types.keys():
            description_template = "Visit the following link (or click above) to report for '{type}':\n{link}"
            embed.url = accepted_types[type]
            embed.description = description_template.format(type=type.capitalize(),link=embed.url)

        await ctx.send(
            "",
            embed=embed,
        )

    @commands.command(aliases=["week", "topbroadcasts"])
    async def topstreams(self, ctx, time_period="week"):
        """
        Get the top broadcasts of a certain time period.
        """
        allowed_time_periods = [
            "hour",
            "day",
            "week",
            "month",
            "year",
            "all",
        ]
        if time_period.lower() in allowed_time_periods:
            top_broadcast = {}
            for subreddit in get_rpan_sub_abbreviations().values():
                for submission in get_reddit().subreddit(subreddit).search("flair_name:\"Broadcast\"", sort="top", time_filter=time_period, limit=1):
                    top_broadcast[subreddit] = submission

            fields = {}
            for subreddit, broadcast in top_broadcast.items():
                if broadcast != None:
                    fields[f"r/{subreddit}"] = f"[{broadcast.title}](https://reddit.com{broadcast.permalink})"

            if fields == {}:
                fields["Problem"] = "The bot was unable to find any top broadcasts within that given time period."

            await ctx.send("", embed=generate_embed(
                title="Top Streams",
                description=f"These are the top broadcasts within the past {time_period}.",
                fields=fields,
            ))

        else:
            await ctx.send("", embed=generate_embed(
                title="Error - Top Streams",
                description="You input an invalid amount of time.",
            ))

def setup(bot):
    bot.add_cog(RPAN(bot))
