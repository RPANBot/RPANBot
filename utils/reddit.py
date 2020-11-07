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
    def __init__(self, settings):
        self.settings = settings

        super().__init__(
            **self.settings.reddit.auth_info,
            user_agent="RPANBot v2.0 (by u/OneUpPotato, u/JayRy27, u/bsoyka, with contributions from GitHub: RPANBot/RPANBot)",
        )
        print(f"Authenticated with Reddit as u/{self.user.me()}")

        # Load the mods list.
        self.refresh_mods()

    def refresh_mods(self):
        self.mods = []
        for subreddit in [self.subreddit(subreddit_name) for subreddit_name in self.settings.reddit.rpan_subreddits]:
            for moderator in subreddit.moderator():
                mod_name = moderator.name.lower()
                if mod_name not in self.mods:
                    self.mods.append(mod_name)

    @property
    def rpan_subreddits(self):
        return self.subreddit("+".join(self.settings.reddit.rpan_subreddits))


loaded_instance = None
def RedditInstance(*args, **kwargs) -> RPANBotReddit:
    global loaded_instance
    if not loaded_instance:
        loaded_instance = RPANBotReddit(*args, **kwargs)
    return loaded_instance
