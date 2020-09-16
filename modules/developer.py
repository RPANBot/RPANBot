# Developer Module
import discord
from discord.ext import commands

from git import cmd
from json import loads
from sys import executable
from os import getcwd, system
from typing import Optional, Union

from utils.database import GuildPrefix, get_db_session
from utils.helpers import generate_embed, is_main_dev
from utils.reddit import get_reddit
from utils.settings import get_discord_key

class Developer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, aliases=["dev"])
    @commands.check(is_main_dev)
    async def developer(self, ctx):
        """
        Development Commands. Only Developers (not Contributors) are authorised to use this.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development",
                    description="You are authorised to use this command, but input an invalid subcommand.",
                    footer_text="None",
                    bot=self.bot,
                    message=ctx.message
                ),
            )

    @developer.group(pass_context=True, name="getprefix", help="Get the bot prefix of a Discord guild.")
    async def developer_getprefix(self, ctx, guild_id: int=0):
        if guild_id == 0:
            guild_id = ctx.guild.id

        try:
            result = get_db_session().query(GuildPrefix).filter_by(guild_id=guild_id).first()
            if result != None:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Get Prefix (Developer)",
                        description="That server is using a custom prefix.",
                        fields={
                            "Default Prefix": self.bot.get_relevant_prefix(),
                            "Custom Prefix": result.guild_prefix,
                        },
                        footer_text=f"Requested by {ctx.author}",
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
            else:
                await ctx.send(
                    "",
                    embed=generate_embed(
                        title="Get Prefix (Developer)",
                        description="That server doesn't have a custom prefix assigned.",
                        fields={
                            "Default Prefix": self.bot.get_relevant_prefix(),
                        },
                        footer_text=f"Requested by {ctx.author}",
                        bot=self.bot,
                        message=ctx.message
                    ),
                )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Get Prefix (Developer)",
                    description="There was a problem getting the prefix for that server.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @developer.group(pass_context=True, name="setprefix", help="Set the bot prefix of a Discord guild.")
    async def developer_setprefix(self, ctx, guild_id: Optional[int]=0, *, prefix):
        if guild_id == 0:
            guild_id = ctx.guild.id

        try:
            result = get_db_session().query(GuildPrefix).filter_by(guild_id=guild_id).first()
            previous_prefix = self.bot.get_relevant_prefix() + " (DEFAULT)"
            if result != None:
                previous_prefix = result.guild_prefix

            self.bot.set_server_prefix(server=guild_id, prefix=prefix)

            await ctx.send(
                "",
                embed=generate_embed(
                    title="Set Prefix (Developer)",
                    description="Succesfuly updated the prefix.",
                    fields={
                        "Default Prefix": self.bot.get_relevant_prefix(),
                        "Previous Prefix": previous_prefix,
                        "New Prefix": prefix,
                    },
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message
                ),
            )
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Set Prefix (Developer)",
                    description="There was a problem setting the prefix for that server.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @developer.group(pass_context=True, name="load", help="Load a module.")
    async def developer_load(self, ctx, module_name):
        try:
            self.bot.calculate_lines_of_code()
            self.bot.load_extension("modules." + module_name)
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Module Load",
                    description=f"Succesfully loaded '{module_name}'.",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        except Exception as e:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Module Load",
                    description=f"Failed to load '{module_name}'.",
                    fields={
                        "Reason": f"{e}",
                    },
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            pass

    @developer.group(pass_context=True, name="unload", help="Unload a module.")
    async def developer_unload(self, ctx, module_name):
        try:
            self.bot.calculate_lines_of_code()
            self.bot.unload_extension("modules." + module_name)
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Module Unload",
                    description=f"Succesfully unloaded '{module_name}'.",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        except Exception as e:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Module Unload",
                    description=f"Failed to unload '{module_name}'.",
                    fields={
                        "Reason": f"{e}",
                    },
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            pass

    @developer.group(pass_context=True, name="reload", help="Reload a module.")
    async def developer_reload(self, ctx, module_name):
        try:
            self.bot.calculate_lines_of_code()
            self.bot.reload_extension("modules." + module_name)
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Module Reload",
                    description=f"Succesfully reloaded '{module_name}'.",
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
        except Exception as e:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Module Reload",
                    description=f"Failed to reload '{module_name}'.",
                    fields={
                        "Reason": f"{e}",
                    },
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            pass

    @developer.group(pass_context=True, name="pull", help="Pulls the latest from 'master' branch.")
    async def developer_pull(self, ctx):
        message = await ctx.send("", embed=generate_embed(title="Development - Pulling from Git", bot=self.bot, message=ctx.message))
        try:
            g = cmd.Git(getcwd())
            g.pull()
            await message.edit(content="", embed=generate_embed(title="Development - Pull Succesful", bot=self.bot, message=ctx.message))
        except:
            await message.edit(
                content="",
                embed=generate_embed(
                    title="Development - Pull Failed",
                    color=discord.Color(0x8B0000),
                    bot=self.bot,
                    message=ctx.message,
                ),
            )
            raise

    @developer.group(pass_context=True, name="restart", help="Restarts the bot.")
    async def developer_restart(self, ctx):
        await ctx.send("", embed=generate_embed(title="Development - Restarting Bot", bot=self.bot, message=ctx.message))
        try:
            await self.bot.close()
        except:
            pass
        finally:
            system(f"{executable} -m pip install --upgrade -r requirements.txt && {executable} main.py")

    @developer.group(pass_context=True, name="restart-nopip", help="Restarts the bot without dependency upgrades from pip.")
    async def developer_restart_nopip(self, ctx):
        await ctx.send("", embed=generate_embed(title="Development - Restarting Bot", description="Skipping dependency upgrades", bot=self.bot, message=ctx.message))
        try:
            await self.bot.close()
        except:
            pass
        finally:
            system(f"{executable} main.py")

    @developer.group(pass_context=True, name="eval", help="Evaluates an expression")
    async def developer_eval(self, ctx, *, expression):
        result = str(eval(expression)).replace(get_discord_key(), "DISCORD BOT KEY")
        await ctx.send(
            "",
            embed=generate_embed(
                title="Eval Result",
                description=f"```\n{result}\n```",
                bot=self.bot,
                message=ctx.message
            ),
        )

    @developer.group(pass_context=True, name="log", help="Get the bot to upload the Discord log.")
    async def developer_log(self, ctx):
        try:
            await ctx.send(f"Requested by {ctx.author.mention}", file=discord.File('discord.log'))
        except:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Log (Developer)",
                    description="There was a problem uploading the log.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message
                ),
            )
            raise

    @developer.error
    async def developer_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CheckFailure):
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Error",
                    description="You aren't authorised to use this.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message
                ),
            )
        else:
            await ctx.send(
                "",
                embed=generate_embed(
                    title="Development - Error",
                    description="Something went wrong.",
                    color=discord.Color(0x8B0000),
                    footer_text=f"Requested by {ctx.author}",
                    bot=self.bot,
                    message=ctx.message
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
            await send_to.send(embed=generate_embed(
                title="Click here to view the RPAN wiki.",
                url=url,
                #footer_text=f"Requested by {ctx.author}",
                bot=self.bot,
                message=ctx.message
            ))

def setup(bot):
    bot.add_cog(Developer(bot))
