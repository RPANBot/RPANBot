# Stream Notifications Module
import discord
import requests

from time import sleep
from json import loads
from threading import Thread

from .utils.reddit import get_reddit
from .utils.helpers import generate_embed, format_timestamp
from .utils.classes import Broadcast, Broadcasts
from .utils.settings import get_error_channel, get_rpan_subreddits
from .utils.database import StreamNotifications, generate_db_session

class BroadcastNotifications:
    def __init__(self, bot):
        self.bot = bot

        Thread(target=self.watch_broadcasts).start()

        print("Watching Broadcasts.")

    async def send_embed_and_message(self, channel, message, embed):
        try:
            fetched_channel = await self.bot.fetch_channel(channel)
            sent_message = await fetched_channel.send(message, embed=embed)

            # Attempt to publish the message.
            try:
                await sent_message.publish()
            except:
                pass
        except Exception as error:
            self.bot.sentry.capture_exception(error)
            print(f"{error}\nError posting message to channel ({channel}).")

    def watch_broadcasts(self):
        # Setup a stream to watch all new items on RPAN subreddits.
        streams_session = generate_db_session()
        for submission in get_reddit().subreddit("+".join(get_rpan_subreddits())).stream.submissions(skip_existing=True):
            try:
                username_db_search_string = f'"{submission.author.name.lower()}"'
                result = streams_session.query(StreamNotifications).filter(StreamNotifications.notifications_usernames.contains(username_db_search_string)).all()
                if len(result) >= 1:
                    broadcasts = Broadcasts()
                    broadcast = broadcasts.has_broadcast(submission.id.replace("t3_",""))
                    if broadcast == False:
                        broadcast = Broadcast(submission.id.replace("t3_",""))

                    # Ensure that the broadcast is not missing any required information.
                    broadcast.check_attributes(set_retry=True)

                    if broadcast.api_status == "success":
                        if submission.author.name.lower() != broadcast.author_name.lower():
                            self.bot.sentry.capture_message(f"STREAM NOTIFICATIONS DEBUG - Detected non matching names from API result.\nNames: {submission.author.name} and {broadcast.author_name}\nBroadcast: {submission.permalink} and {broadcast.url}")
                            continue

                        for notification_settings in result:
                            # Notification Keyword Check
                            if notification_settings.notifications_keywords not in [None, "[]", ""]:
                                keywords = loads(notification_settings.notifications_keywords)
                                if not any(keyword in broadcast.title.lower() for keyword in keywords):
                                    continue

                            # Send Notification
                            self.bot.loop.create_task(
                                self.send_embed_and_message(
                                    notification_settings.notifications_channel_id,
                                    ("" if notification_settings.notifications_custom_text == None else notification_settings.notifications_custom_text),
                                    generate_embed(
                                        title=f"u/{broadcast.author_name} started streaming!",
                                        url=broadcast.url,
                                        fields={
                                            "Title": broadcast.title,
                                            "Subreddit": f"r/{broadcast.subreddit_name}",
                                        },
                                        thumbnail=broadcast.thumbnail,
                                        footer_text=f"Started: {format_timestamp(broadcast.published_at)}",
                                    )
                                ),
                            )
                    else:
                        self.bot.sentry.capture_message(f"STREAM NOTIFICATIONS DEBUG - Unsuccesful API result.\nStatus: {broadcast.api_status}\nAuthor: {submission.author.name}\nPermalink: {submission.permalink}")
            except Exception as e:
                print(e)
                self.bot.sentry.capture_exception(e)

                sleep(60)
                self.watch_broadcasts()
                self.bot.sentry.capture_message("Restarted watching broadcasts.")
                return

def setup(bot):
    BroadcastNotifications(bot)
