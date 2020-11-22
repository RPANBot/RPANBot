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
from quart import current_app, session, redirect, request, url_for

from typing import Union
from functools import wraps

from expiringdict import ExpiringDict
from requests_oauthlib import OAuth2Session

from web.helpers.classes import User, UnauthedUser


class UserHandler:
    def __init__(self, app) -> None:
        self.authed_users = ExpiringDict(max_len=50, max_age_seconds=3600)

        app.user_handler = self
        self.unauthed_user = UnauthedUser()

        self.app = app
        self.app.context_processor(self.template_context)

    async def auth_user(self) -> None:
        """
        Handle authenticating a user on the callback response.
        """
        if not session.get("DISCORD_STATE"):
            return redirect(url_for('main.login'))

        discord = self.base_session(state=session["DISCORD_STATE"])
        token = discord.fetch_token(
            "https://discord.com/api/oauth2/token",
            client_secret=self.app.core.settings.discord.client_secret,
            authorization_response=request.url
        )

        # Ensure that we have the required scopes.
        if "identify" not in token.get("scope", []) or "guilds" not in token.get("scope", []):
            return redirect(url_for('main.login'))

        # Fetch the info and authenticate the user.
        user_payload = discord.get("https://discord.com/api/users/@me").json()
        guilds_payload = discord.get("https://discord.com/api/users/@me/guilds").json()

        user_id = int(user_payload["id"])
        if self.app.core.bot.is_excluded_user(user_id):
            return redirect(url_for("home.main"))

        self.authed_users[user_id] = User(user_payload, guilds_payload)

        session["DISCORD_ID"] = user_id
        session["DISCORD_TOKEN"] = token

        # Bring the user to the dashboard.
        return redirect(url_for("dashboard.main"))

    def deauth_user(self, user_id: int = None) -> None:
        """
        Deauthenticates a user.
        If an id isn't given, then we are able to delete the session cookies from the user.
        """
        if user_id is None:
            if session.get("DISCORD_ID") in self.authed_users.keys():
                del self.authed_users[session["DISCORD_ID"]]
            session.pop("DISCORD_ID", None)
            session.pop("DISCORD_TOKEN", None)
        else:
            self.authed_users.pop(user_id, None)

    def get_user(self) -> Union[User, UnauthedUser]:
        user_id = session.get("DISCORD_ID")
        if user_id:
            if user_id in self.authed_users:
                return self.authed_users[user_id]

            # No valid user was found, so deauth the user.
            self.deauth_user()
        return self.unauthed_user

    def get_bot_invite(self) -> str:
        if self.get_user().is_real:
            # TODO: Callback to refesh guild list.
            return "https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={invite_permissions}".format(
                client_id=self.app.core.settings.discord.client_id,
                invite_permissions=self.app.core.settings.discord.invite_permissions,
            )
        else:
            return "https://discord.com/oauth2/authorize?client_id={client_id}&scope=bot&permissions={invite_permissions}".format(
                client_id=self.app.core.settings.discord.client_id,
                invite_permissions=self.app.core.settings.discord.invite_permissions,
            )

    def template_context(self) -> dict:
        return {
            "user": self.get_user(),
            "invite_link": self.get_bot_invite(),
            "support_invite": self.app.core.settings.links.support_guild,
        }

    def base_session(self, token: dict = None, state: str = None, scopes: list = None) -> OAuth2Session:
        return OAuth2Session(
            token=token,
            state=state,
            scope=scopes,

            client_id=self.app.core.settings.discord.client_id,
            auto_refresh_kwargs={
                "client_id": self.app.core.settings.discord.client_id,
                "client_secret": self.app.core.settings.discord.client_secret,
            },
            redirect_uri=self.app.core.settings.web.redirect_uri,

            auto_refresh_url="https://discord.com/api/oauth2/token",
            token_updater=self.token_update,
        )

    def token_update(self, token: dict) -> None:
        session["DISCORD_TOKEN"] = token


def authed_only(function):
    @wraps(function)
    async def wrapper(*args, **kwargs):
        if current_app.user_handler.get_user().is_real:
            return await function(*args, **kwargs)
        else:
            return redirect(url_for("home.login"))

    return wrapper
