from discord import Embed

from time import sleep
from requests import get

from typing import Union

from json import loads, dumps

from .helpers import format_timestamp
from .settings import get_rpan_subreddits
from .database import BNSetting, get_db_session

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

class BroadcastNotifSettingsHandler:
    def __init__(self):
        # Stores which broadcast notifications setting is currently selected by the guild.
        # A local id is the id of a broadcast notification setting inside the guild list.
        self.selections = {}
        self.guild_notif_channel_limits = {}

    def current_selection(self, guild_id: int) -> int:
        """
        Get the currently selected stream notifications channel.
        :param guild_id: The guild to check the selection for.
        :return: The local id of the selection.
        """
        if guild_id in self.selections.keys():
            return self.selections[guild_id]
        return 1

    def current_limit(self, guild_id: int) -> int:
        """
        Get the current limit for notification channels on a guild.
        Currently there are no guilds with set channel limits, so this will just return 25.
        :param guild_id: The guild to check.
        :return: The amount of channels the guild can have notification channels setup on.
        """
        if guild_id in self.guild_notif_channel_limits.keys():
            return self.guild_notif_channel_limits[guild_id]
        return 25

    def query_settings(self, guild_id: int, channel_id: int = None):
        """
        Query for the notification settings on a specified guild.
        :param guild_id: The guild to get the settings on.
        :return: The result from the query.
        """
        if channel_id == None:
            return get_db_session().query(BNSetting).filter_by(guild_id=guild_id)
        else:
            return get_db_session().query(BNSetting).filter_by(guild_id=guild_id, channel_id=channel_id)

    def get_notif_setting(self, guild_id: int, channel_id: int) -> Union[BNSetting, None]:
        """
        Get a specific notification setting for a channel.
        :param guild_id: The guild to get the settings for.
        :param channel_id: The channel to get the settings for.
        :return: Either the result, or None.
        """
        query_result = self.query_settings(guild_id, channel_id)
        return query_result.first()

    def get_notif_settings(self, guild_id: int) -> Union[list, None]:
        """
        Get the notification settings for a guild.
        :param guild_id: The guild to get the settings for.
        :return: Either a list of the results, or none.
        """
        query_result = self.query_settings(guild_id)
        if query_result.count() >= 1:
            return query_result.all()
        else:
            return None

    def get_notif_settings_count(self, guild_id: int) -> int:
        """
        Get the number of notification settings for a guild.
        :param guild_id: The guild to get the settings for.
        :return: The amount of notification settings there.
        """
        query_result = self.query_settings(guild_id)
        return query_result.count()

    def get_notif_setting_by_id(self, guild_id: int, selection_id: int) -> Union[BNSetting, None]:
        """
        Get a notification setting for a guild using either the local id or channel id.
        :param guild_id: The guild to get the setting for.
        :param selection_id: Either a local id or a channel id.
        :return: The notification setting that was found, or none.
        """
        notif_settings = self.get_notif_settings(guild_id)
        if notif_settings == None:
            return None

        # Check if the selection_id is within the range of the list.
        # If it is then it is a local id, if not then it might be a channel id.
        handling_id = int(selection_id) - 1
        if handling_id in range(len(notif_settings)):
            return notif_settings[handling_id]

        # Query for a setting for that guild id and channel id, then return.
        return self.get_notif_setting(guild_id, selection_id)

    def parse_id_to_local(self, guild_id: int, id: int) -> Union[int, None]:
        """
        Checks an id (which could either be a guild id or a 'local' id) and return the 'local' id.
        :param id: The id to parse.
        :return: The 'local' id (if there are any settings) or none.
        """
        notif_setting = self.get_notif_setting_by_id(guild_id, id)
        if notif_setting == None:
            return None

        notif_settings = self.get_notif_settings(guild_id)
        for i, bn_setting in enumerate(notif_settings):
            if bn_setting == notif_setting:
                return i

class BNList:
    """
    The parent class for broadcast notification list attributes (currently: usernames and keywords).
    """
    def __init__(self, init_item: Union[str, None]):
        init_item = "[]" if init_item in [None, ""] else init_item
        self.items = loads(init_item)

    def add(self, item: str) -> bool:
        """
        Adds an item to the list.
        :param item: The item to add.
        :return: Whether or not the item was added.
        """
        item = item.lower()
        if item not in self.items:
            self.items.append(item)
            return True
        return False

    def remove(self, item: str) -> bool:
        """
        Adds an item to the list.
        :param item: The item to remove.
        :return: Whether or not the item was removed.
        """
        item = item.lower()
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def __str__(self) -> str:
        return dumps(self.items)

class BNUsernamesAttr(BNList):
    """
    The broadcast notification usernames list attribute.
    """
    def __init__(self, usernames_str: Union[str, None]):
        super().__init__(init_item=usernames_str)

class BNKeywordsAttr(BNList):
    """
    The broadcast notification keyword list attribute.
    """
    def __init__(self, keywords_str: Union[str, None]):
        super().__init__(init_item=keywords_str)
