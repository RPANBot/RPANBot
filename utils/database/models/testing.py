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
from sqlalchemy import Column, Integer, String

from utils.database.models.base import Base


class BNTestingDataset(Base):
    __tablename__ = "bn_dataset_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(25), unique=True)

    def __repr__(self):
        return f"BNTestingDataset({self.id}, {self.username})"
