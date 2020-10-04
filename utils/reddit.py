import praw

class RPANBotReddit(praw.Reddit):
    def __init__(self, settings):
        self.settings = settings

        # Initiate the Reddit instance.
        super().__init__(
            **self.settings.reddit.auth_info,
            user_agent="RPANBot v1.5 (original by u/OneUpPotato, contributions by RPAN-Moderators/RPANBot)",
        )
        print(f"Logged into Reddit as u/{self.user.me()}")

        # Load the mods list.
        self.refresh_mods()

    def refresh_mods(self):
        self.mods = set()
        for subreddit in [self.subreddit(subreddit_name) for subreddit_name in self.settings.reddit.rpan_subreddits]:
            for moderator in subreddit.moderator():
                self.mods.add(moderator.name.lower())
        self.mods = list(self.mods)

    @property
    def rpan_subreddits(self):
        return self.subreddit("+".join(self.settings.reddit.rpan_subreddits))

    @property
    def mqmm_subreddits(self):
        return self.subreddit("+".join(self.settings.reddit.mqmm_settings.keys()))
