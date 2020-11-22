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
from sqlalchemy import Column, BigInteger, Integer, String
from sqlalchemy.orm import relationship

from utils.database.decorators import JsonDecorator

from utils.database.models.base import Base


class BNUser(Base):
    __tablename__ = "bn_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(25), unique=True)

    notifications_for = relationship("BNSetting", secondary="bn_mapped_users", back_populates="users", lazy="dynamic")

    def __repr__(self):
        return f"BNUser({self.id}, {self.username})"


class BNSetting(Base):
    __tablename__ = "bn_settings"

    id = Column(Integer, primary_key=True)

    guild_id = Column(BigInteger)
    channel_id = Column(BigInteger, unique=True)
    webhook_url = Column(String, unique=True)

    custom_text = Column(String)
    keyword_filters = Column(JsonDecorator)
    subreddit_filters = Column(JsonDecorator)

    users = relationship("BNUser", secondary="bn_mapped_users", back_populates="notifications_for", lazy="dynamic")

    def __repr__(self):
        return f"BNSetting({self.guild_id})"
