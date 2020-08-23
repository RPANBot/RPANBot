# Mod Queue/Mod Mail Notifier Module
from time import sleep
from threading import Thread
from asyncio import run_coroutine_threadsafe

import discord
from discord import Color
from praw.models import Submission

from .utils.reddit import get_reddit
from .utils.helpers import generate_embed
from .utils.settings import get_mqmm_settings

class MQMMNotifications:
    def __init__(self, bot):
        self.bot = bot

        if len(get_mqmm_settings()) >= 1:
            Thread(target=self.watch_queue).start()
            Thread(target=self.watch_modmail).start()

            print("Watching MM and MQ.")
        else:
            print("No MQMM settings detected.")

    async def send_embed(self, channel, embed):
        fetched_channel = await self.bot.fetch_channel(channel)
        await fetched_channel.send(embed=embed)

    def watch_queue(self):
        try:
            for item in get_reddit().subreddit("+".join(get_mqmm_settings().keys())).mod.stream.modqueue(skip_existing=True):
                subreddit_name = item.subreddit.display_name.lower()
                if subreddit_name in get_mqmm_settings().keys():
                    print(f"{subreddit_name} - Detected {item} in the Mod Queue")
                    run_coroutine_threadsafe(
                        self.send_embed(
                            get_mqmm_settings()[subreddit_name],
                            generate_embed(
                                title="Mod Queue - New Item (r/{})".format(subreddit_name), url="https://reddit.com{}".format(item.permalink), color=Color(0x517185),
                                fields={
                                    "ID": "``{}``".format(item.id),
                                    "Type": "``{}``".format(("Submission" if isinstance(item, Submission) else "Comment")),
                                    "Author": "``u/{}``".format(item.author.name),
                                    "Title" if isinstance(item, Submission) else "Body": "``{}``".format((item.title if isinstance(item, Submission) else item.body)),
                                },
                                footer_text="None",
                            )
                        ),
                        self.bot.loop,
                    )
        except Exception as e:
            print(e)
            self.bot.sentry.capture_exception(e)

            if str(e) == "received 403 HTTP response":
                print("Not authorised to watch queue.")
                return

            sleep(60)
            self.watch_queue()
            return

    def watch_modmail(self):
        try:
            for conversation in get_reddit().subreddit("+".join(get_mqmm_settings().keys())).mod.stream.modmail_conversations(skip_existing=True):
                message = conversation.messages[len(conversation.messages) - 1]
                subreddit_name = conversation.owner.display_name.lower()
                if subreddit_name in get_mqmm_settings().keys():
                    print(f"{subreddit_name} - Detected new modmail message")
                    run_coroutine_threadsafe(
                        self.send_embed(
                            get_mqmm_settings()[subreddit_name],
                            generate_embed(
                                title="Mod Mail - New Message (r/{})".format(subreddit_name), url="https://mod.reddit.com/mail/all/{}".format(conversation.id), color=Color(0x7BBDBF),
                                fields={
                                    "Conversation ID": "``{}``".format(conversation.id),
                                    "Author": "``u/{}``".format(message.author.name),
                                    "Subject": "``{}``".format(conversation.subject),
                                    "Message": "``{}``".format(message.body_markdown),
                                },
                                footer_text="None",
                            )
                        ),
                        self.bot.loop,
                    )
        except Exception as e:
            print(e)
            self.bot.sentry.capture_exception(e)

            if str(e) == "received 403 HTTP response":
                print("Not authorised to watch modmail.")
                return

            sleep(60)
            self.watch_modmail()
            pass

def setup(bot):
    MQMMNotifications(bot)
