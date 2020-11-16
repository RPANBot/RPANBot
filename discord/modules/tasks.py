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
from discord.ext.commands import Cog
from discord.ext.tasks import loop


class Tasks(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.web_task.start()

    def cog_unload(self) -> None:
        self.web_task.cancel()

    @loop()
    async def web_task(self) -> None:
        await self.bot.core.handle_web()

    @web_task.before_loop
    async def before_web_task(self) -> None:
        await self.bot.wait_until_ready()

def setup(bot) -> None:
    bot.add_cog(Tasks(bot))
