from typing import Union
from datetime import datetime, timezone

def format_prefix(prefix) -> str:
    """
    Returns the default/custom prefix from a list of prefixes.

    :param prefix: This can either be a single prefix or a list of prefixes.
    :return: The custom/default prefix (not a bot mention).
    """
    if isinstance(prefix, str):
        return prefix
    else:
        return prefix[2]

def format_timestamp(timestamp) -> str:
    """
    Formats a timestamp. This is used by the broadcast notifications.

    :param timestamp: The timestamp to format.
    :return: Returns a timestamp in a set format.
    """
    time = datetime.fromtimestamp(int(timestamp / 1000), tz=timezone.utc)
    return time.strftime("%d/%m/%Y at %H:%M UTC")

def parse_username(username: str) -> str:
    """
    Parses an input username.
    :return: The username, in lowercase, without '/u/' or 'u/'.
    """
    return username.replace("/u/", "").replace("u/", "").lower()

def parse_id(string: str) -> Union[int, None]:
    """
    Parses a string to turn a mention (if there's one) into an id.
    :return: The filtered id.
    """
    try:
        return int("".join([char for char in string if char.isdigit()]))
    except ValueError:
        return None
