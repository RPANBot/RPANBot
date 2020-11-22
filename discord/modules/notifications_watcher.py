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
from discord.ext.commands import Cog, command

from praw.models import Submission
from prawcore import PrawcoreException

from time import sleep
from threading import Thread

from json import dumps
from requests import post

from utils.database.models.testing import BNTestingDataset
from utils.database.models.broadcast_notifications import BNSetting, BNUser

from discord.helpers.utils import escape_username, is_rpan_broadcast, format_timestamp


class NotificationsWatcher(Cog):
    """
    This cog watches for new Reddit posts and sends broadcast notifications based on them.
    """
    def __init__(self, bot) -> None:
        self.bot = bot

        self.submissions_stream = Thread(target=self.watch_submissions)
        self.submissions_stream.start()

    def send_broadcast_notification(self, setting: BNSetting, broadcast) -> None:
        escaped_username = escape_username(broadcast.author_name)
        data = dumps({
            "username": "RPANBot",
            "avatar_url": self.bot.core.settings.links.bot_avatar,
            "content": ("" if not setting.custom_text else setting.custom_text),
            "embeds": [
                {
                    "title": f"u/{escaped_username} started streaming!",
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

        request = post(
            setting.webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
            },
        )

        if request.status_code in [200, 204]:
            print("BN: Succesfully messaged a stream notification.")
        else:
            print("BN: Problem messaging using webhook.")

    def watch_submissions(self) -> None:
        """
        Watches for new submissions on the RPAN community subreddits.
        Handles broadcast notifications.
        """
        db_session = self.bot.core.db_handler.Session()

        watching = True
        while watching:
            try:
                submission: Submission
                for submission in self.bot.core.reddit.rpan_subreddits.stream.submissions(skip_existing=True):
                    if not is_rpan_broadcast(submission.url):
                        continue

                    author = submission.author.name.lower()

                    # Fetch the settings for this user (if any).
                    notifications_for = []
                    result = db_session.query(BNUser).filter_by(username=author).first()
                    if result:
                        for notif_setting in result.notifications_for.all():
                            notifications_for.append(notif_setting)

                    # Check if the user is in the broadcast notifications testing dataset.
                    # If they are then send a notification to all channels with 'rpanbot' added.
                    if db_session.query(BNTestingDataset).filter_by(username=author).first():
                        result = [user.notifications_for.all for user in db_session.query(BNUser).filter_by(username="rpanbot").all()]
                        for notif_setting in result:
                            notifications_for.append(notif_setting)

                    # Continue if there aren't any settings for this user.
                    if not len(notifications_for):
                        continue

                    # Attempt to fetch the broadcast object from the Strapi.
                    broadcast = self.bot.core.strapi.get_broadcast(submission.id)
                    if broadcast is None:
                        broadcast = self.bot.core.strapi.submission_to_broadcast(submission)

                    # Check each setting requirement, and send notifications to those where it fits.
                    for setting in notifications_for:
                        # Ensure that the broadcast has the required keyword filters (if the setting has that).
                        if setting.keyword_filters:
                            title = broadcast.title.lower()
                            if not any(keyword in title for keyword in setting.keyword_filters):
                                continue

                        # Check that the broadcast is in an accepted subreddit (if there are subreddit_filters).
                        if setting.subreddit_filters:
                            subreddit = submission.subreddit.display_name.lower()
                            if subreddit not in setting.subreddit_filters:
                                continue

                        # Send a notification.
                        self.send_broadcast_notification(setting, broadcast)
            except PrawcoreException as e:
                print(f"SUBMISSIONS WATCHER: {e} - PRAW error raised.")
                sleep(15)
            except SystemExit:
                watching = False
                return
            except Exception as e:
                if self.bot.core.sentry:
                    self.bot.core.sentry.capture_exception(e)
                print(f"SUBMISSIONS WATCHER: Error raised {e}.")


def setup(bot) -> None:
    bot.add_cog(NotificationsWatcher(bot))
