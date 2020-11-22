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
from typing import Optional, Union

from utils.database.models.broadcast_notifications import BNSetting


class BNSettingsHandler:
    def __init__(self, bot) -> None:
        """
        Store which broadcast notifications setting is currently selected by guild.
        A local id is the id of a broadcast notification setting inside the guild's local list.
        """
        self.bot = bot
        self.selections = {}

    def get_current_selection(self, guild_id: int) -> int:
        """
        Gets the currently selected broadcast notification channel.
        :param guild_id: The guild to check the selection for.
        :return: The local id of the current selection.
        """
        if guild_id in self.selections.keys():
            return self.selections[guild_id]
        return 1

    def get_channel_limit(self, guild_id: int) -> int:
        """
        Get the current limit for notification channels on a guild.
        :param guild_id: The guild to check.
        :return: 25. Currently there are no guilds with set channel limits.
        """
        return 25

    def query_settings(self, guild_id: int, channel_id: Optional[int] = None):
        """
        Query for all notification settings on a guild or a specific channel notification setting.
        :param guild_id: The guild to get the setting on.
        :param channel_id: An optional paramater to get a specific channel setting.
        :return: The result from the query.
        """
        if channel_id is not None:
            return self.bot.db_session.query(BNSetting).filter_by(guild_id=guild_id, channel_id=channel_id)
        else:
            return self.bot.db_session.query(BNSetting).filter_by(guild_id=guild_id).order_by(BNSetting.id)

    def get_setting(self, guild_id: int, channel_id: int) -> Union[None, BNSetting]:
        """
        Get a specific notification setting on a guild.
        :param guild_id: The guild to get the setting on.
        :param channel_id: The channel id (not local id) of the channel to fetch.
        :return: Either the settings or None.
        """
        query_result = self.query_settings(guild_id, channel_id)
        return query_result.first()

    def get_settings(self, guild_id: int) -> Union[list, None]:
        """
        Get all notification settings on a guild.
        :param guild_id: The guild to get the settings on.
        :return: Either the settings or None.
        """
        query_result = self.query_settings(guild_id)
        if query_result.count() >= 1:
            return query_result.all()
        return None

    def get_settings_count(self, guild_id: int) -> int:
        """
        Get the current amount of notification settings on a guild.
        :return: The amount of settings, for that guild, in the database.
        """
        query_result = self.query_settings(guild_id)
        return query_result.count()

    def get_by_either_id(self, guild_id: int, selection_id: int) -> Union[None, BNSetting]:
        """
        Get a setting by either the local ID or full channel id.
        :param guild_id: The guild to get the setting for.
        :param selection_id: Either a local id or a channel id.
        :return: None or the notification setting that was found.
        """
        notif_settings = self.get_settings(guild_id)
        if notif_settings is None:
            return None

        # Check if the selection_id is within the range of the list.
        # If it is then we'll handle it as a local id. If not then it may be a full channel id.
        handling_id = int(selection_id) - 1
        if handling_id in range(len(notif_settings)):
            return notif_settings[handling_id]

        # Query for a setting checking by channel id.
        return self.get_setting(guild_id, selection_id)

    def id_to_local(self, guild_id: int, selection_id: int) -> Union[None, int]:
        """
        Checks a selection_id (which could be either a guild id or local id) and returns the local id.
        :param id: The id to parse.
        :return: The local id or None.
        """
        notif_setting = self.get_by_either_id(guild_id, selection_id)
        if notif_setting is None:
            return None

        notif_settings = self.get_settings(guild_id)
        for i, bn_setting in enumerate(notif_settings):
            if bn_setting == notif_setting:
                return i
        return None

    def get_current_setting(self, guild_id: int) -> Union[None, BNSetting]:
        """
        Gets the currently selected notification setting.
        :return: The currently selected setting or None.
        """
        current_selection = self.get_current_selection(guild_id)
        setting = self.get_by_either_id(guild_id, current_selection)
        return setting
