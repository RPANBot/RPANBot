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
import praw


class RPANBotReddit(praw.Reddit):
    def __init__(self, core) -> None:
        self.core = core

        self.user_agent = "RPANBot v2.1 (by u/OneUpPotato, u/JayRy27 and u/bsoyka - GitHub: RPANBot/RPANBot)"
        super().__init__(
            **self.core.settings.reddit.auth_info,
            user_agent=self.user_agent,
        )
        print(f"Authenticated with Reddit as u/{self.user.me()}")

    @property
    def rpan_subreddits(self) -> praw.models.Subreddit:
        return self.subreddit("+".join(self.core.rpan_subreddits.list))

    def is_valid_user(self, redditor: praw.models.Redditor) -> bool:
        try:
            redditor.id
            return True
        except Exception:
            return False


loaded_instance = None
def RedditInstance(*args, **kwargs) -> RPANBotReddit:
    global loaded_instance
    if not loaded_instance:
        loaded_instance = RPANBotReddit(*args, **kwargs)
    return loaded_instance
