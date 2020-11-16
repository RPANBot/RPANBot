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
from praw.models import Submission

from time import sleep
from typing import Union
from requests import get, Response
from datetime import datetime, timezone

from expiringdict import ExpiringDict

from discord.helpers.utils import is_rpan_broadcast

from utils.strapi_models import Broadcast, Broadcasts


class StrapiWrapper:
    def __init__(self, core) -> None:
        self.core = core
        self.praw = self.core.reddit
        self.settings = self.core.settings

        self.top_broadcasts_cache = ExpiringDict(max_len=3, max_age_seconds=300)

        self.base_url = "https://strapi.reddit.com/"

    def get_headers(self) -> dict:
        return {
            "User-Agent": self.praw.user_agent,
            "Cache-Control": "no-cache",
        }

    def handle_request(self, endpoint: str) -> Response:
        """
        Send a request to the Strapi with the headers.
        :return: The response given.
        """
        return get(
            url=self.base_url + endpoint,
            headers=self.get_headers(),
        )

    def fetch_broadcast(self, id: str) -> Union[Broadcast, None]:
        """
        Fetch a broadcast by id.
        :return: The broadcast class or None.
        """
        request = self.handle_request("broadcasts/" + id)
        if request.json()["status"] == "success":
            payload = request.json()["data"]
            payload["source"] = "strapi"

            return Broadcast(payload=payload)
        return None

    def fetch_broadcasts(self) -> Union[Broadcasts, None]:
        """
        Fetch all of the current broadcasts.
        :return: The broadcasts fetched or None.
        """
        request = self.handle_request("broadcasts")
        if request.json()["status"] == "success":
            broadcasts = []
            if len(request.json()["data"]):
                for broadcast in request.json()["data"]:
                    payload = broadcast
                    payload["source"] = "strapi"
                    broadcasts.append(Broadcast(payload=payload))

                return Broadcasts(contents=broadcasts)
        return None

    def get_broadcast(self, id: str) -> Union[Broadcast, None]:
        """
        Attempt to fetch and retrieve a broadcast.
        :return: The retrieved broadcast or None.
        """
        broadcast = self.fetch_broadcast(id)
        if broadcast is not None:
            return broadcast

        # Attempt to fetch the broadcast again.
        sleep(10)
        return self.fetch_broadcast(id)

    def get_broadcasts(self) -> Union[Broadcasts, None]:
        """
        Attempt to fetch and retrieve the active broadcasts.
        :note: Maybe memoize this for 30 seconds or so.
        :return: The retrieved broadcasts or None.
        """
        broadcasts = self.fetch_broadcasts()
        if broadcasts is not None:
            return broadcasts

        # Attempt to fetch the broadcasts again.
        sleep(10)
        return self.fetch_broadcasts()

    def get_last_broadcast(self, username: str) -> Union[Broadcast, None]:
        """
        Get the last broadcast of a user.
        :return: The found last broadcast or None.
        """
        user = self.praw.redditor(username)
        if not self.praw.is_valid_user(user):
            return None

        for submission in user.submissions.new(limit=25):
            if is_rpan_broadcast(submission.url):
                return self.submission_to_broadcast(submission)
        return None

    def get_top_broadcasts(self, time_period: str = None) -> tuple:
        """
        Get the top broadcast on each subreddit (from within a specific time period)
        :return: A tuple of the top broadcasts in each subreddit and the time period used.
        """
        allowed_time_periods = [
            "hour",
            "day",
            "week",
            "month",
            "year",
            "all",
        ]

        if time_period:
            time_period = time_period.lower()

        if time_period not in allowed_time_periods:
            time_period = "week"

        if time_period in self.top_broadcasts_cache:
            return self.top_broadcasts_cache[time_period], time_period
        else:
            top_broadcasts = {}
            for subreddit in self.core.rpan_subreddits.list:
                for submission in self.praw.subreddit(subreddit).search("flair_name:\"Broadcast\"", sort="top", time_filter=time_period, limit=1):
                    top_broadcasts[subreddit] = submission

            self.top_broadcasts_cache[time_period] = top_broadcasts
            return top_broadcasts, time_period

    def submission_to_broadcast(self, submission: Submission) -> Union[Broadcast, None]:
        """
        Turn a PRAW submission into a broadcast class.
        :return: The broadcast class.
        """
        return Broadcast(payload={
            "post": {
                "id": submission.fullname,
                "title": submission.title,
                "url": submission.url,
                "authorInfo": {
                    "name": submission.author.name
                },
                "subreddit": {
                    "name": submission.subreddit.display_name
                }
            },
            "stream": {
                "state": "IS_LIVE",  # TODO: Switch stream state
                "publish_at": submission.created_utc,
            }
        })

    def format_broadcast_timestamp(self, timestamp: int) -> str:
        """
        Formats a timestamp. This is used by the broadcast notifications.
        :param timestamp: The timestamp to format.
        :return: Returns a timestamp in a set format.
        """
        return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)


loaded_instance = None
def StrapiInstance(*args, **kwargs) -> StrapiWrapper:
    global loaded_instance
    if not loaded_instance:
        loaded_instance = StrapiWrapper(*args, **kwargs)
    return loaded_instance
