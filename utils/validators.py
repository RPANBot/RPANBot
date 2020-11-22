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
from re import UNICODE, compile


def is_valid_prefix(prefix: str) -> bool:
    """
    Checks if a bot custom prefix is valid.
    :return: Whether it is or not.
    """
    if not len(prefix) or len(prefix) >= 10:
        return False

    if "`" in prefix:
        return False

    return True


def is_valid_reddit_username(username: str) -> bool:
    """
    Checks if a username is an accepted Reddit username.
    :return: A boolean of if it is or not.
    """
    if len(username) < 3 or len(username) > 20:
        return False

    username_pattern = compile(r"\A[\w-]+\Z", UNICODE)
    if not username_pattern.match(username):
        return False

    return True
