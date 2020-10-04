# Stream Notifications Module
import requests

from time import sleep
from threading import Thread

from requests import post
from json import loads, dumps

from utils.helpers import format_timestamp
from utils.classes import Broadcast, Broadcasts
from utils.database import BNSetting, generate_db_session

class BroadcastNotifications:
    def __init__(self, bot):
        self.bot = bot

        Thread(target=self.watch_broadcasts).start()
        print("Watching Broadcasts.")

    def send_broadcast_notification(self, bn_setting, broadcast):
        try:
            data = dumps({
                "username": "RPANBot",
                "avatar_url": self.bot.settings.links.bot_avatar,
                "content": ("" if bn_setting.custom_text == None else bn_setting.custom_text),
                "embeds": [
                    {
                        "title": f"u/{broadcast.author_name} started streaming!",
                        "url": broadcast.url,
                        "color": 26763,
                        "fields": [
                            {
                                "name": "Title",
                                "value": broadcast.title,
                                "inline": True,
                            },
                            {
                                "name": "Subreddit",
                                "value": f"r/{broadcast.subreddit_name}",
                                "inline": True,
                            }
                        ],
                        "footer": {
                            "text": f"Started: {format_timestamp(broadcast.published_at)}",
                        },
                        "thumbnail": {
                            "url": broadcast.thumbnail,
                        },
                    },
                ],
            })
            request = post(bn_setting.webhook_url, data=data, headers={"Content-Type":"application/json"})
            if request.status_code in [200, 204]:
                print("Succesfully messaged a stream notification.")
            else:
                print("Problem messaging using webhook.")
        except Exception as e:
            self.bot.sentry.capture_exception(e)
            print(f"Error posting using webhook: {e}.")

    def watch_broadcasts(self):
        # Setup a stream to watch all new items on RPAN subreddits.
        session = generate_db_session()
        for submission in self.bot.reddit.rpan_subreddits.stream.submissions(skip_existing=True):
            try:
                username = submission.author.name.lower()
                username_search_string = f'"{username}"'
                result = session.query(BNSetting).filter(BNSetting.usernames.contains(username_search_string)).all()
                if username in self.bot.reddit.mods:
                    result.append(session.query(BNSetting).filter(BNSetting.usernames.contains(f'"rpanbot"')).all())

                if len(result) >= 1:
                    broadcasts = Broadcasts()
                    broadcast = broadcasts.has_broadcast(submission.id.replace("t3_",""))
                    if broadcast == False:
                        broadcast = Broadcast(submission.id.replace("t3_",""))

                    # Ensure that the broadcast is not missing any required information.
                    broadcast.check_attributes(set_retry=True)

                    if broadcast.api_status == "success":
                        if submission.author.name.lower() != broadcast.author_name.lower():
                            self.bot.sentry.capture_message(f"NOTIFS DEBUG\nDetected non matching names from API result.\nNames: {submission.author.name} and {broadcast.author_name}\nBroadcast: {submission.permalink} and {broadcast.url}")
                            continue

                        for bn_setting in result:
                            # Notification Keyword Check
                            if bn_setting.keywords not in [None, "[]", ""]:
                                keywords = loads(bn_setting.keywords)
                                if not any(keyword in broadcast.title.lower() for keyword in keywords):
                                    continue

                            self.send_broadcast_notification(bn_setting, broadcast)
                    else:
                        self.bot.sentry.capture_message(f"NOTIFS DEBUG\nUnsuccesful API result.\nStatus: {broadcast.api_status}\nAuthor: {submission.author.name}\nPermalink: {submission.permalink}")
            except Exception as e:
                print(e)
                self.bot.sentry.capture_exception(e)

                sleep(60)
                self.watch_broadcasts()
                self.bot.sentry.capture_message("Restarted watching broadcasts.")
                return

def setup(bot):
    BroadcastNotifications(bot)
