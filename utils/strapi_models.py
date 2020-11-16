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
from typing import Union


class Broadcast:
    def __init__(self, payload: dict) -> None:
        self.id = payload["post"]["id"]

        self.title = payload["post"]["title"]
        self.url = payload["post"]["url"]

        if payload["post"]["authorInfo"]:
            self.author_name = payload["post"]["authorInfo"]["name"]
        else:
            self.author_name = "[deleted]"

        if payload["post"]["subreddit"]:
            self.subreddit_name = payload["post"]["subreddit"]["name"]
        else:
            self.subreddit_name = self.url.split("/")[5]

        self.published_at = payload["stream"]["publish_at"]

        if payload["stream"]["state"] == "IS_LIVE":
            self.is_live = True
        else:
            self.is_live = False

        if payload.get("source", None) == "strapi":
            self.published_at = int(self.published_at) / 1000

            self.global_rank = payload["global_rank"]
            self.total_streams = payload["total_streams"]

            self.unique_watchers = payload["unique_watchers"]
            self.continuous_watchers = payload["continuous_watchers"]

            self.thumbnail = payload["stream"]["thumbnail"]
        else:
            self.thumbnail = ""

            self.global_rank = "Err"
            self.total_streams = "Err"
            self.unique_watchers = "Err"
            self.continuous_watchers = "Err"

    def __repr__(self) -> str:
        return f"Broadcast({self.id})"


class Broadcasts:
    def __init__(self, contents: list = None) -> None:
        self.broadcasts = []
        if contents:
            self.broadcasts = contents

    def top_broadcast(self, subreddit: str = None) -> Union[Broadcast, None]:
        """
        Get the top broadcast.
        :param subreddit: Optional paramater to find the top broadcast on a specific subreddit.
        :return: The broadcast or None.
        """
        if not len(self.broadcasts):
            return None

        if subreddit is None:
            return self.broadcasts[0]
        else:
            subreddit = subreddit.lower()
            for broadcast in self.broadcasts:
                if broadcast.subreddit_name.lower() == subreddit:
                    return broadcast
        return None

    def has_broadcast(self, id: str) -> Union[Broadcast, bool]:
        """
        Checks if the broadcast list contains a broadcast with a specified id.
        :param id: The id of the broadcast.
        :return: The broadcast or False.
        """
        for broadcast in self.broadcasts:
            if broadcast.id == id:
                return broadcast
        return False

    def has_streamer(self, name: str) -> Union[Broadcast, bool]:
        """
        Checks if the broadcast list contains a broadcast from a specified user.
        :param name: The streamer to search for.
        :return: The broadcast or False.
        """
        name = name.lower()
        for broadcast in self.broadcasts:
            if broadcast.author_name.lower() == name:
                return broadcast
        return False

    def __repr__(self) -> str:
        return f"Broadcasts({', '.join(repr(broadcast) for broadcast in self.broadcasts)})"
