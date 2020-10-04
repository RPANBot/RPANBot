# Mod Queue/Mod Mail Notifier Module
from praw.models import Submission

from time import sleep
from threading import Thread
from asyncio import run_coroutine_threadsafe

from utils.classes import RPANEmbed

class MQMMNotifications:
    def __init__(self, bot):
        self.bot = bot

        if len(self.bot.settings.reddit.mqmm_settings) >= 1:
            Thread(target=self.watch_queue).start()
            Thread(target=self.watch_modmail).start()

            print("Watching MM and MQ.")
        else:
            print("No MQMM settings detected.")

    async def send_embed(self, channel, embed):
        fetched_channel = await self.bot.find_channel(channel)
        await fetched_channel.send(embed=embed)

    def watch_queue(self):
        try:
            for item in self.bot.reddit.mqmm_subreddits.mod.stream.modqueue(skip_existing=True):
                subreddit_name = item.subreddit.display_name.lower()
                print(f"{subreddit_name} - Detected {item} in the Mod Queue")
                run_coroutine_threadsafe(
                    self.send_embed(
                        self.bot.settings.reddit.mqmm_settings[subreddit_name],
                        RPANEmbed(
                            title=f"Mod Queue - New Item (r/{subreddit_name})",
                            url=f"https://reddit.com{item.permalink}",
                            fields={
                                "ID": f"``{item.id}``",
                                "Type": "``{}``".format(("Submission" if isinstance(item, Submission) else "Comment")),
                                "Author": f"``u/{item.author.name}``",
                                "Title" if isinstance(item, Submission) else "Body": "``{}``".format((item.title if isinstance(item, Submission) else item.body)),
                            },
                            colour=0x517185,
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
            for conversation in self.bot.reddit.mqmm_subreddits.mod.stream.modmail_conversations(skip_existing=True):
                message = conversation.messages[len(conversation.messages) - 1]
                subreddit_name = conversation.owner.display_name.lower()
                print(f"{subreddit_name} - Detected new modmail message")
                run_coroutine_threadsafe(
                    self.send_embed(
                        self.bot.settings.reddit.mqmm_settings[subreddit_name],
                        RPANEmbed(
                            title=f"Mod Mail - New Message (r/{subreddit_name})",
                            url=f"https://mod.reddit.com/mail/all/{conversation.id}",
                            fields={
                                "Conversation ID": f"``{conversation.id}``",
                                "Author": f"``u/{message.author.name}``",
                                "Subject": f"``{conversation.subject}``",
                                "Message": f"``{message.body_markdown}``",
                            },
                            colour=0x7BBDBF,
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
