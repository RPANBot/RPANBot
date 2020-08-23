from discord.ext.tasks import loop
from discord.ext.commands import Cog

from time import time
from requests import post

from .utils.settings import get_statuspage_key

class StatusModule(Cog):
    def __init__(self, bot):
        self.bot = bot

        if get_statuspage_key():
            self.sender.start()

    def cog_unload(self):
        self.sender.cancel()

    @loop(minutes=2.5)
    async def sender(self):
        post(
            url="https://api.statuspage.io/v1/pages/jcw1p1vt0d38/metrics/csfszhh5p54x/data",
            params={"data[timestamp]": int(time()), "data[value]": self.bot.latency * 1000},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": "OAuth " + get_statuspage_key(),
            },
        )

def setup(bot):
    bot.add_cog(StatusModule(bot))
