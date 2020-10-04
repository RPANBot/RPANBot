from discord.ext.commands import CheckFailure

class DeveloperCheckFailure(CheckFailure):
    """
    This exception is raised when a non-developer attempts to perform a developer-only action.
    """
    pass

class GuildNotifsLimitExceeded(Exception):
    """
    This exception is raised when something attempts to go over the guild broadcast notifications limit.
    """
    pass
