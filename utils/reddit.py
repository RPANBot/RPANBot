import praw
from .settings import get_reddit_login_info

reddit = praw.Reddit(
    **get_reddit_login_info(),
    user_agent="RPANBot v1.4 (original by u/OneUpPotato, contributions by RPAN-Moderators/RPANBot)",
)
print(f"Logged into Reddit as u/{reddit.user.me()}")

def get_reddit():
    return reddit
