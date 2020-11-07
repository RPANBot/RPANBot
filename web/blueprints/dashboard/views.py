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
from quart import Blueprint, current_app, render_template, redirect, url_for

from web.helpers.user_handler import authed_only


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard", template_folder="templates")

@dashboard_bp.route("/")
async def main():
    return await render_template("dashboard/main.html")


@dashboard_bp.route("/refresh/")
@authed_only
async def refresh():
    # Refeshes a user's guilds.
    # TODO: Add a cooldown instead of only allowing them to refresh once per login.
    user = current_app.user_handler.get_user()
    user.refresh()
    return redirect(url_for("dashboard.main"))


@dashboard_bp.route("/guild/<int:id>/")
@authed_only
async def guild(id: int):
    user = current_app.user_handler.get_user()
    if id in user.guilds_mapping.keys():
        guild = user.guilds_mapping[id]
        return str(vars(guild))
    else:
        return redirect(url_for("dashboard.main"))
