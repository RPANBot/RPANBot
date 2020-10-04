import sentry_sdk

def init_sentry(sentry_link) -> None:
    sentry_sdk.init(sentry_link)

def get_sentry() -> sentry_sdk:
    return sentry_sdk
