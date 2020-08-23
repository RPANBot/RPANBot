import sentry_sdk

def init_sentry(sentry_link):
    sentry_sdk.init(sentry_link)

def get_sentry():
    return sentry_sdk
