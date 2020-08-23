from os import getenv
from yaml import safe_load
from dotenv import load_dotenv

config = {}
def load_configs(file_path):
    global config
    """
    Load the required configuration files.
    :param file_path: The path to the main project folder.
    """

    # Load the env file.
    load_dotenv(dotenv_path=file_path + "/.env", verbose=True)

    # Load the config file.
    try:
        with open("config.yml", "r") as config_file:
            config = safe_load(config_file.read())
    except Exception as e:
        print(f"{e} - Problem loading the config file.")
        exit()

    # Parse the config.
    config["rpan_subreddits"]["list"] = [subreddit.lower() for subreddit in config["rpan_subreddits"]["list"]]
    config["rpan_subreddits"]["abbreviations"] = dict((abbreviation.lower(), subreddit.lower()) for abbreviation, subreddit in config["rpan_subreddits"]["abbreviations"].items())
    config["mqmm_notifications"] = dict((subreddit.lower(), channel_id) for subreddit, channel_id in config["mqmm_notifications"].items())

    print("Succesfully loaded the settings.")

# Authentication
def get_reddit_login_info():
    # Gets the Reddit login information from the loaded env file.
    return {
        "client_id": getenv("REDDIT_CLIENT_ID"),
        "client_secret": getenv("REDDIT_CLIENT_SECRET"),
        "refresh_token": getenv("REDDIT_REFRESH_TOKEN"),
    }

def get_discord_key():
    # Gets the Discord bot token.
    return getenv("BOT_DISCORD_KEY")

# Subreddits
def get_mqmm_settings():
    return config["mqmm_notifications"]

def get_rpan_subreddits():
    return config["rpan_subreddits"]["list"]

def get_rpan_sub_abbreviations():
    return config["rpan_subreddits"]["abbreviations"]

# Channels
def get_join_leave_channel():
    return getenv("BOT_JOIN_LEAVE_CHANNEL")

def get_error_channel():
    return getenv("BOT_ERROR_CHANNEL")

def get_bug_reports_channel():
    return getenv("BOT_BUG_REPORTS_CHANNEL")

def get_approved_bugs_channel():
    return getenv("BOT_APPROVED_BUGS_CHANNEL")

def get_denied_bugs_channel():
    return getenv("BOT_DENIED_BUGS_CHANNEL")

# Other
def get_default_prefix():
    # Get the bot's default prefix.
    return getenv("BOT_PREFIX")

def get_sentry_link():
    # Get the Sentry error tracking link.
    return getenv("SENTRY_LINK")

def get_statuspage_key():
    # Get the statuspage API key. (not required)
    return getenv("STATUSPAGE_API_KEY")

def get_config():
    return config
