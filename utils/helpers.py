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
from utils.database.models.custom_prefixes import CustomPrefixes
from utils.database.models.broadcast_notifications import BNSetting


def erase_guild_settings(session, id: int) -> None:
    notif_settings = session.query(BNSetting).filter_by(guild_id=id).all()
    if notif_settings:
        for notif_setting in notif_settings:
            session.delete(notif_setting)

    custom_prefixes = session.query(CustomPrefixes).filter_by(guild_id=id).first()
    if custom_prefixes:
        session.delete(custom_prefixes)

    session.commit()


def to_lowercase(text: str) -> str:
    return text.lower()


def parse_reddit_username(name: str) -> str:
    return name.lower().replace("/u/", "").replace("u/", "")
