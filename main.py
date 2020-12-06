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
from glob import glob

from pygount import ProjectSummary, SourceAnalysis

from utils.settings import Settings
from utils.sentry import start_sentry
from utils.reddit import RedditInstance
from utils.strapi_wrapper import StrapiInstance
from utils.rpan_subreddits import RPANSubreddits
from utils.database.handler import DatabaseHandler

from discord.bot import RPANBot
from web.quart import create_app


class RPANBotCore:
    def __init__(self) -> None:
        # Load the settings.
        self.settings = Settings()
        self.rpan_subreddits = RPANSubreddits()

        # Calculate the lines of code.
        self.calculate_loc()

        # Load the Sentry error tracking module.
        self.sentry = None
        if self.settings.links.sentry:
            self.sentry = start_sentry(link=self.settings.links.sentry)

        # Load the database handler.
        self.db_handler = DatabaseHandler(settings=self.settings)

        # Initiate PRAW and the custom strapi wrapper.
        self.reddit = RedditInstance(core=self)
        self.strapi = StrapiInstance(core=self)

        # Initiate the web and bot instances.
        self.web = create_app(core=self)
        self.bot = RPANBot(core=self)

        # Start the bot.
        self.bot.start_bot()

    async def handle_web(self) -> None:
        """
        Creates the Quart task on the Discord bot event loop.
        """
        await self.web.run_task(host="0.0.0.0", port=5050, use_reloader=False)

    def calculate_loc(self) -> None:
        """
        Calculates the number of lines of code that the bot uses.
        """
        project_summary = ProjectSummary()
        for source_path in glob("**/*.py", recursive=True) + glob("**/*.html", recursive=True):
            source_analysis = SourceAnalysis.from_file(source_path, "pygount", encoding="utf-8", fallback_encoding="cp850")
            project_summary.add(source_analysis)

        self.lines_of_code = 0
        for language_summary in project_summary.language_to_language_summary_map.values():
            self.lines_of_code += language_summary.code_count


if __name__ == "__main__":
    RPANBotCore()
