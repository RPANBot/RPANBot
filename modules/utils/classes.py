from time import sleep
from requests import get

from .helpers import format_timestamp
from .settings import get_rpan_subreddits

class Broadcast:
    def __init__(self, id=None, broadcast_info=None, retry=False):
        """
        Initiate a Broadcast class.

        :param id: The id of the broadcast.
        :param broadcast_info: Sometimes provided to the object instead of having to fetch it.
        :param retry: Whether the bot should retry fetching info on an API error.
        """

        # Set the defaults.
        self.retry_on_failure = retry
        self.already_retried = False

        # Set the class id to the provided broadcast id.
        self.id = id

        # Check if broadcast info has been provided already.
        if broadcast_info == None:
            # Request the broadcast information from the api.
            request_json = self.request_broadcast_json()
            self.api_status = request_json["status"]
        else:
            # Broadcast info has already been provided.
            self.api_status = "success"
            if self.id == None:
                self.id = broadcast_info["post"]["id"].replace("t3_","")

        self.is_live = False
        self.is_broadcast = False
        if self.api_status == "success":
            broadcast_info = request_json["data"] if broadcast_info == None else broadcast_info
            self.set_attributes(broadcast_info)
        else:
            if retry:
                self.retry()

    def request_broadcast_json(self):
        """
        Requests the broadcast information from the API.
        :return: JSON of the broadcast info.
        """
        request = get(f"https://strapi.reddit.com/broadcasts/{self.id}", headers={"Cache-Control": "no-cache"})
        return request.json()

    def check_attributes(self, broadcast_info=None, set_retry=False):
        """
        Validates that the info has everything that's required.
        :param broadcast_info: The information to check from.
        :param set_retry: Whether the bot should retry if any information is missing.
        """
        if set_retry:
            self.retry_on_failure = True

        try:
            published_at = None
            if isinstance(broadcast_info, dict):
                published_at = broadcast_info["stream"]["publish_at"]
            else:
                published_at = self.published_at

            format_timestamp(published_at)
        except:
            self.api_status = "missing required attributes"
            if self.retry_on_failure:
                self.retry()

    def set_attributes(self, broadcast_info):
        """
        Sets the attributes of the Broadcast object.
        :param broadcast_info: The information to parse.
        """
        # Ensure that the required information is here.
        self.check_attributes(broadcast_info)

        if self.api_status == "success":
            self.is_broadcast = True
            self.is_live = True if broadcast_info["stream"]["state"] == "IS_LIVE" else False

            self.url = broadcast_info["post"]["url"]

            self.author_name = "[deleted]"
            try:
                self.author_name = broadcast_info["post"]["authorInfo"]["name"]
            except:
                pass

            self.subreddit_name = "[error]"
            try:
                self.subreddit_name = broadcast_info["post"]["subreddit"]["name"]
            except:
                self.subreddit_name = self.url.split("/")[5]
                pass

            self.title = broadcast_info["post"]["title"]

            self.published_at = broadcast_info["stream"]["publish_at"]

            self.global_rank = broadcast_info["global_rank"]
            self.total_streams = broadcast_info["total_streams"]

            self.unique_watchers = broadcast_info["unique_watchers"]
            self.continuous_watchers = broadcast_info["continuous_watchers"]

            self.thumbnail = broadcast_info["stream"]["thumbnail"]

    def refresh_information(self):
        # Make another call to the strapi.
        request_json = self.request_broadcast_json()
        self.api_status = request_json["status"]

        # If it's a success, set the attributes.
        if self.api_status == "success":
            self.set_attributes(request_json["data"])

    def retry(self):
        if not self.already_retried:
            self.already_retried = True
            sleep(2.5)
            self.refresh_information()

    def __repr__(self):
        return f"Broadcast({self.id})"

class Broadcasts:
    def __init__(self, starting_broadcasts=None):
        self.broadcasts = []
        if starting_broadcasts != None:
            self.broadcasts = starting_broadcasts

        self.api_status = "failure"

        if len(self.broadcasts) == 0:
            request = get("https://strapi.reddit.com/broadcasts", headers={"Cache-Control": "no-cache"})
            request_json = request.json()

            self.api_status = request_json["status"]
            if self.api_status == "success":
                for broadcast_info in request_json["data"]:
                    self.broadcasts.append(Broadcast(broadcast_info=broadcast_info))
        else:
            self.api_status = "success"

    def get_top(self, subreddit=None):
        if len(self.broadcasts) >= 1:
            if subreddit == None:
                return self.broadcasts[0]
            else:
                subreddit = subreddit.lower()
                for broadcast in self.broadcasts:
                    if broadcast.subreddit_name.lower() == subreddit:
                        return broadcast
                return None
        else:
            return None

    def has_broadcast(self, id):
        for broadcast in self.broadcasts:
            if broadcast.id == id:
                return broadcast
        return False

    def has_streamer(self, name):
        name = name.lower()
        for broadcast in self.broadcasts:
            if broadcast.author_name.lower() == name:
                return broadcast
        return False

    def __repr__(self):
        return f"Broadcasts({', '.join([str(item) for item in self.broadcasts])})"

class PushshiftBroadcasts:
    def __init__(self, username):
        request = get(f"https://api.pushshift.io/reddit/submission/search?author={username}&subreddit={','.join(get_rpan_subreddits())}&filter=id,link_flair_text")
        request_data = request.json()["data"]

        self.broadcasts_ids = []
        if len(request_data) >= 1:
            user_streams_ids = []
            for stream in request_data:
                try:
                    if stream["link_flair_text"].lower().strip() == "broadcast":
                        self.broadcasts_ids.append(stream["id"])
                except:
                    pass

    def find_undeleted(self):
        if len(self.broadcasts_ids) >= 1:
            for stream_id in self.broadcasts_ids[0:4]:
                broadcast = Broadcast(stream_id)
                if broadcast.api_status == "success":
                    if broadcast.author_name != "[deleted]":
                        return broadcast
        return None

    def __repr__(self):
        return f"Broadcasts({', '.join([str(item) for item in self.broadcasts])})"
