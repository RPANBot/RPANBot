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
from pathlib import Path

from pygount import ProjectSummary, SourceAnalysis

from utils.settings import Settings
from utils.reddit import RedditInstance

from discord.bot import RPANBot
from web.quart import create_app


class RPANBotCore:
    def __init__(self) -> None:
        # Load the settings.
        self.settings = Settings(file_path=Path(__file__).parent.absolute())

        # Initiate the Reddit, bot and web instances.
        self.reddit = RedditInstance(settings=self.settings)
        self.web = create_app(core=self)
        self.bot = RPANBot(core=self)

        # Calculate the lines of code.
        self.calculate_loc()

        # Start the bot.
        self.start_web()
        self.bot.start_bot()

    def start_web(self) -> None:
        """
        Creates the Quart task on the Discord bot event loop.
        """
        self.bot.loop.create_task(self.web.run_task(host="0.0.0.0", port=5050, use_reloader=False))

    def calculate_loc(self) -> None:
        """
        Calculates the number of lines of code that the bot uses.
        """
        project_summary = ProjectSummary()
        for source_path in glob("**/*.py", recursive=True):
            source_analysis = SourceAnalysis.from_file(source_path, "pygount", encoding="utf-8", fallback_encoding="cp850")
            project_summary.add(source_analysis)

        self.lines_of_code = 0
        for language_summary in project_summary.language_to_language_summary_map.values():
            self.lines_of_code += language_summary.code_count


if __name__ == "__main__":
    RPANBotCore()
