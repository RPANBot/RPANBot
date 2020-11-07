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
from quart import Quart, send_from_directory

from os import environ
from os.path import join

from web.helpers.globals import get_guild_icon
from web.helpers.user_handler import UserHandler

from web.blueprints.home.views import home_bp
from web.blueprints.dashboard.views import dashboard_bp


def create_app(core) -> Quart:
    app = Quart(__name__)
    app.core = core

    app.config.update(core.settings.web.config)
    if core.settings.web.config["DEBUG"]:
        environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"

    UserHandler(app)

    @app.route('/favicon.ico')
    async def favicon():
        return await send_from_directory(
            join(app.root_path, "static"),
            "imgs/favicon.ico",
            mimetype="image/vnd.microsoft.icon"
        )

    app.jinja_env.globals["get_guild_icon"] = get_guild_icon

    app.register_blueprint(home_bp)
    app.register_blueprint(dashboard_bp)

    return app
