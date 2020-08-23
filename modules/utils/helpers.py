from discord import Color, Embed, Message

from requests import post
from math import ceil, floor, log
from datetime import datetime, timezone

from .settings import get_config

def format_prefix(prefix):
    """
    Returns the default/custom prefix from a list of prefixes.

    :param prefix: This can either be a single prefix or a list of prefixes.
    :return: The custom/default prefix (not a bot mention).
    """
    if isinstance(prefix, str):
        return prefix
    else:
        return prefix[2]

# Embed
def generate_embed(
    title: str,
    description: str = "",
    url: str = "",
    color: Color = Color(0x00688B),
    fields: dict = {},
    thumbnail: str = "Unspecified",
    footer_text: str = "Unspecified",
    bot = None,
    message: Message = None
) -> Embed:
    """
    A standard way for the bot to generate an embed.

    :param title: The embed's title.
    :param description: The embed's description.
    :param url: The title URL.
    :param color: The color of the embed.
    :param fields: The embed's field (given as a dict)
    :param thumbnail: The thumbnail that the embed should use.
    :param footer_text: Text that should be used in the embed's footer.
    :param bot: The bot instance. This is used to get the custom prefix.
    :param message: The message. This is used to get the custom prefix.
    :return: An embed generated to the specifications.
    """

    embed = Embed(title=title, description=description, url=url, color=color)

    for key, value in fields.items():
        embed.add_field(name=key, value=value)

    if thumbnail != "Unspecified":
        embed.set_thumbnail(url=thumbnail)

    if footer_text != "Unspecified" and footer_text != "None":
        if message != None:
            embed.set_footer(text=f"{footer_text} - Bot by {bot.get_relevant_prefix(message)}contributors")
        else:
            embed.set_footer(text=footer_text)
    elif footer_text != "None":
        if message != None:
            embed.set_footer(text=f"Bot by {bot.get_relevant_prefix(message)}contributors")

    return embed

def format_timestamp(timestamp):
    """
    Formats a timestamp. This is used by the broadcast notifications.

    :param timestamp: The timestamp to format.
    :return: Returns a timestamp in a set format.
    """
    time = datetime.fromtimestamp(int(timestamp / 1000), tz=timezone.utc)
    return time.strftime("%d/%m/%Y at %H:%M UTC")

# Main Developer Check
async def is_main_dev(ctx):
    return ctx.author.id in get_config()["bot_developer_ids"]

# Official RPAN Discord Guild
async def is_rpan_guild(ctx):
    return ctx.guild.id in get_config()["rpan_guilds"]

# RPAN Bot Guilds
async def is_rpan_bot_guild(ctx):
    return ctx.guild.id in get_config()["bot_support_guilds"]
