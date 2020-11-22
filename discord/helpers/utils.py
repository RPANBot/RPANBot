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
from re import sub
from datetime import datetime, timezone


def is_rpan_broadcast(link: str) -> bool:
    if "reddit.com/rpan/" in link:
        return True
    else:
        return False


def parse_link(link: str) -> str:
    """
    Parse the stream id from a provided link.
    :return: The parsed stream id.
    """
    id = (
        sub("http(s)?://", "", link)
        .replace("www.reddit.com/", "")
        .replace("old.reddit.com/", "")
        .replace("reddit.com/", "")
        .replace("redd.it/", "")
    )
    return sub("(rpan/r|r)/(.*?)/(comments/)?", "", id).split("/")[0].split("?")[0]


def escape_username(name: str) -> str:
    """
    Escapes markdown in a username.
    :return: The username with prevented italics.
    """
    return name.replace("_", "\\_")


def format_timestamp(timestamp: float) -> str:
    """
    Formats a timestamp.
    :param timestamp: The timestamp to format.
    :return: Returns a time in a set format.
    """
    time = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
    return time.strftime("%d/%m/%Y at %H:%M UTC")
