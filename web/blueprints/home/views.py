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
from quart import Blueprint, current_app, render_template, redirect, session, url_for


home_bp = Blueprint("home", __name__, url_prefix="/", template_folder="templates")

@home_bp.route("/")
async def main():
    return await render_template("home/main.html")


@home_bp.route("/features/")
async def features():
    return await render_template("home/features.html")


@home_bp.route("/privacy/")
async def privacy():
    return await render_template("home/privacy.html")


@home_bp.route("/credits/")
async def credits():
    return await render_template("home/credits.html")


@home_bp.route("/login/")
async def login():
    auth_url, state = current_app.user_handler.base_session(scopes=["identify", "guilds"]).authorization_url("https://discord.com/api/oauth2/authorize")
    session["DISCORD_STATE"] = state
    return redirect(auth_url)


@home_bp.route("/callback/")
async def callback():
    return await current_app.user_handler.auth_user()


@home_bp.route("/logout/")
async def logout():
    current_app.user_handler.deauth_user()
    return redirect(url_for("home.main"))
