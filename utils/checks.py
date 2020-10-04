from utils.errors import DeveloperCheckFailure

async def is_main_dev(ctx) -> bool:
    """
    Checks if a user is a main bot developer.
    :return: Whether or not they are listed as one in the settings.
    """
    if ctx.author.id in ctx.bot.settings.ids.bot_developers:
        return True
    else:
        raise DeveloperCheckFailure

async def is_rpan_guild(ctx) -> bool:
    """
    Checks if the guild is a main RPAN guild.
    :return: Whether or not it is (as listed in the settings).
    """
    return ctx.guild.id in ctx.bot.settings.ids.rpan_guilds

async def is_rpan_bot_guild(ctx) -> bool:
    """
    Checks if the guild is one of the RPANBot guilds. This is used for the bot support commands.
    :return: Whether or not it is (as listed in the settings).
    """
    return ctx.guild.id in ctx.bot.settings.ids.support_guilds
