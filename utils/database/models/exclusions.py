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
from sqlalchemy import Column, BigInteger, Integer

from utils.database.models.base import Base


class ExcludedGuild(Base):
    __tablename__ = "excluded_guilds"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True)

    def __repr__(self):
        return f"ExcludedGuild({self.guild_id})"


class ExcludedUser(Base):
    __tablename__ = "excluded_users"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True)

    def __repr__(self):
        return f"ExcludedUser({self.user_id})"
