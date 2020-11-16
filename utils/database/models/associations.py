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
from sqlalchemy import Column, Integer, ForeignKey

from utils.database.models.base import Base


class BNMappedUser(Base):
    __tablename__ = "bn_mapped_users"

    user_id = Column(Integer, ForeignKey("bn_users.id"), primary_key=True)
    setting_id = Column(Integer, ForeignKey("bn_settings.id"), primary_key=True)

    def __repr__(self):
        return f"BNMappedUser({self.setting_id}, {self.setting_id})"
