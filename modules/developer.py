# Developer Module
import discord
from discord.ext import commands

from git import cmd
from json import loads
from sys import executable, argv
from typing import Optional, Union
from os import getcwd, system, execl

from utils.classes import RPANEmbed
from utils.checks import is_main_dev
from utils.database import GuildPrefix, get_db_session

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=["dev"])
    @commands.check(is_main_dev)
    async def developer(self, ctx):
        """
        Development Commands. Only the Core Developers are authorised to use this.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development",
                    description="You are authorised to use this command, but input an invalid subcommand.",
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @developer.group(name="subreddits", help="View the RPAN subreddits listed in the settings.")
    async def developer_subreddits(self, ctx):
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="RPAN Subreddits List (Developer)",
                description="The loaded subreddits in the configuration are:",
                fields={
                    "List": "\n".join(self.bot.settings.reddit.rpan_subreddits),
                    "Abbreviations": "\n".join([f"{abbrv}: {subreddit}" for abbrv, subreddit in self.bot.settings.reddit.rpan_sub_abbreviations.items()]),
                },
                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @developer.group(name="getprefix", help="Get the bot prefix of a Discord guild.")
    async def developer_getprefix(self, ctx, guild_id: int = None):
        if guild_id == None:
            guild_id = ctx.guild.id

        try:
            result = get_db_session().query(GuildPrefix).filter_by(guild_id=guild_id).first()
            if result != None:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Get Prefix (Developer)",
                        description="That server is using a custom prefix.",
                        fields={
                            "Default Prefix": self.bot.get_relevant_prefix(),
                            "Custom Prefix": result.guild_prefix,
                        },
                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    ),
                )
            else:
                await ctx.send(
                    "",
                    embed=RPANEmbed(
                        title="Get Prefix (Developer)",
                        description="That server doesn't have a custom prefix assigned.",
                        fields={
                            "Default Prefix": self.bot.get_relevant_prefix(),
                        },
                        user=ctx.author,
                        bot=self.bot,
                        message=ctx.message,
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Get Prefix (Developer)",
                    description="There was a problem getting the prefix for that server.",
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            raise

    @developer.group(name="setprefix", help="Set the bot prefix of a Discord guild.")
    async def developer_setprefix(self, ctx, guild_id: Optional[int] = None, *, prefix):
        if guild_id == None:
            guild_id = ctx.guild.id

        try:
            result = get_db_session().query(GuildPrefix).filter_by(guild_id=guild_id).first()
            previous_prefix = self.bot.get_relevant_prefix() + " (DEFAULT)"
            if result != None:
                previous_prefix = result.guild_prefix

            self.bot.set_server_prefix(server=guild_id, prefix=prefix)

            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Set Prefix (Developer)",
                    description="Succesfuly updated the prefix.",
                    fields={
                        "Default Prefix": self.bot.get_relevant_prefix(),
                        "Previous Prefix": previous_prefix,
                        "New Prefix": prefix,
                    },
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        except:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Set Prefix (Developer)",
                    description="There was a problem setting the prefix for that server.",
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            raise

    @developer.group(name="load", help="Load a module.")
    async def developer_load(self, ctx, module_name):
        try:
            self.bot.calculate_lines_of_code()
            self.bot.load_extension("modules." + module_name)
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Load",
                    description=f"Succesfully loaded '{module_name}'.",
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        except Exception as e:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Load",
                    description=f"Failed to load '{module_name}'.",
                    fields={
                        "Reason": f"{e}",
                    },
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            pass

    @developer.group(name="unload", help="Unload a module.")
    async def developer_unload(self, ctx, module_name):
        try:
            self.bot.calculate_lines_of_code()
            self.bot.unload_extension("modules." + module_name)
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Unload",
                    description=f"Succesfully unloaded '{module_name}'.",
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        except Exception as e:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Unload",
                    description=f"Failed to unload '{module_name}'.",
                    fields={
                        "Reason": f"{e}",
                    },
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            pass

    @developer.group(name="reload", help="Reload a module.")
    async def developer_reload(self, ctx, module_name):
        try:
            self.bot.calculate_lines_of_code()
            self.bot.reload_extension("modules." + module_name)
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Reload",
                    description=f"Succesfully reloaded '{module_name}'.",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        except Exception as e:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Module Reload",
                    description=f"Failed to reload '{module_name}'.",
                    fields={
                        "Reason": f"{e}",
                    },
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            pass

    @developer.group(name="pull", help="Pulls the latest from 'master' branch.")
    async def developer_pull(self, ctx):
        message = await ctx.send(
            "",
            embed=RPANEmbed(
                title="Development - Pulling from Git"
            )
        )
        try:
            g = cmd.Git(getcwd())
            g.pull()
            await message.edit(
                "",
                embed=RPANEmbed(
                    title="Development - Pull Succesful"
                )
            )
        except:
            await message.edit(
                content="",
                embed=RPANEmbed(
                    title="Development - Pull Failed",
                    colour=0x8B0000,
                ),
            )
            raise

    @developer.group(name="restart", help="Restarts the bot.")
    async def developer_restart(self, ctx):
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Development - Restarting Bot"
            )
        )
        try:
            await self.bot.close()
        except:
            pass
        finally:
            system(f"{executable} -m pip install --upgrade -r requirements.txt")
            execl(executable, executable, *argv)

    @developer.group(name="restart-nopip", help="Restarts the bot without dependency upgrades from pip.")
    async def developer_restart_nopip(self, ctx):
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Development - Restarting Bot",
                description="Skipping dependency upgrades"
            )
        )
        try:
            await self.bot.close()
        except:
            pass
        finally:
            execl(executable, executable, *argv)

    @developer.group(name="eval", help="Evaluates an expression")
    async def developer_eval(self, ctx, *, expression):
        result = str(eval(expression)).replace(self.bot.settings.discord_key, "DISCORD BOT KEY")
        await ctx.send(
            "",
            embed=RPANEmbed(
                title="Eval Result",
                description=f"```\n{result}\n```",
                user=ctx.author,
                bot=self.bot,
                message=ctx.message,
            ),
        )

    @developer.group(name="log", help="Get the bot to upload the Discord log.")
    async def developer_log(self, ctx):
        try:
            await ctx.send(
                f"Requested by {ctx.author.mention}",
                file=discord.File('discord.log')
            )
        except:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Log (Developer)",
                    description="There was a problem uploading the log.",
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            raise

    @developer.error
    async def developer_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CheckFailure):
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Error",
                    description="You aren't authorised to use this.",
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        else:
            await ctx.send(
                "",
                embed=RPANEmbed(
                    title="Development - Error",
                    description="Something went wrong.",
                    colour=0x8B0000,
                    user=ctx.author,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

    @developer.group(name="say", help="Send a message as the bot.")
    async def developer_say(self, ctx, send_to: Optional[Union[discord.TextChannel, discord.Member, discord.User]] = None, *, text: str):
        if send_to == None:
            send_to = ctx.channel

        try:
            await ctx.message.delete()
        except:
            pass
        finally:
            await send_to.send(text)

    @developer.group(name="delete", help="Delete a message sent by the bot.")
    async def developer_delete(self, ctx, channel: Optional[discord.TextChannel] = None, *, message_id: int):
        if channel == None:
            channel = ctx.channel

        try:
            fetched_message = await channel.fetch_message(message_id)
            await fetched_message.delete()
        except:
            pass

        try:
            await ctx.message.delete()
        except:
            pass

    @developer.group(name="wikiroll")
    async def developer_wikiroll(self, ctx, send_to: Optional[Union[discord.TextChannel, discord.Member, discord.User]] = None, *, url: str):
        """
        Put any link on the wiki embed.
        """
        if send_to == None:
            send_to = ctx.channel

        try:
            await ctx.message.delete()
        except:
            pass
        finally:
            await send_to.send(
                "",
                embed=RPANEmbed(
                    title="Click here to view the RPAN wiki.",
                    url=url,
                    bot=self.bot,
                    message=ctx.message,
                ),
            )

def setup(bot):
    bot.add_cog(Developer(bot))
