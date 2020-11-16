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
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from utils.database.models.base import Base

from utils.database.models.associations import BNMappedUser
from utils.database.models.custom_prefixes import CustomPrefixes
from utils.database.models.broadcast_notifications import BNSetting, BNUser
from utils.database.models.exclusions import ExcludedGuild, ExcludedUser
from utils.database.models.testing import BNTestingDataset


class DatabaseHandler:
    def __init__(self, settings) -> None:
        self.engine = create_engine(
            "postgresql://{user}:{password}@{host}:{port}/{db}".format(
                host=settings.database.host,
                port=settings.database.port,
                db=settings.database.db,
                user=settings.database.user,
                password=settings.database.password,
            ),
            echo=False
        )

        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

        Base.metadata.create_all(self.engine, checkfirst=True)
