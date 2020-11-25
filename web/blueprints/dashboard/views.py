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
from quart import Blueprint, current_app, flash, render_template, redirect, request, url_for

from discord import AsyncWebhookAdapter, Webhook

from aiohttp import ClientSession

from web.helpers.user_handler import authed_only

from utils.helpers import parse_reddit_username
from utils.validators import is_valid_prefix, is_valid_reddit_username

from utils.database.models.custom_prefixes import CustomPrefixes
from utils.database.models.broadcast_notifications import BNUser, BNSetting


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
        return await render_template("dashboard/guild.html", guild=guild)
    else:
        return redirect(url_for("dashboard.main"))


@dashboard_bp.route("/guild/<int:id>/general/")
@authed_only
async def guild_general(id: int):
    user = current_app.user_handler.get_user()
    if id in user.guilds_mapping.keys():
        guild = user.guilds_mapping[id]

        if not guild.user_has_access():
            return "No Permissions"

        custom_prefixes = current_app.db_session.query(CustomPrefixes).filter_by(guild_id=guild.id).first()
        if custom_prefixes is not None:
            custom_prefixes = custom_prefixes.prefixes

        return await render_template("dashboard/guild_general.html", guild=guild, custom_prefixes=custom_prefixes)
    else:
        return redirect(url_for("dashboard.main"))


@dashboard_bp.route("/guild/<int:id>/general/prefix/", methods=["POST"])
@authed_only
async def guild_general_prefix(id: int):
    user = current_app.user_handler.get_user()
    if id in user.guilds_mapping.keys():
        guild = user.guilds_mapping[id]

        if not guild.user_has_access():
            return "No Permissions"

        # Fetch the form info.
        await request.get_data()
        form = await request.form

        # Handle removing a prefix.
        remove_prefix = form.get("remove", False)
        if remove_prefix:
            prefix = remove_prefix

            result = current_app.db_session.query(CustomPrefixes).filter_by(guild_id=id).first()
            if result is not None:
                prefixes = list(result.prefixes)

                if prefix in prefixes:
                    if len(prefixes) > 1:
                        prefixes.remove(prefix)
                        result.prefixes = prefixes
                    else:
                        current_app.db_session.delete(result)

                    current_app.db_session.commit()

                    if id in current_app.core.bot.prefix_cache:
                        del current_app.core.bot.prefix_cache[id]

                    await flash(u"Deleted that prefix. 🙂👍", "success")
                else:
                    await flash(u"That prefix was not found.", "danger")

                return redirect(url_for("dashboard.guild_general", id=id))
            else:
                await flash(u"No custom prefixes were found.", "danger")
                return redirect(url_for("dashboard.guild_general", id=id))

        # Handle adding a prefix.
        add_prefix = form.get("add_prefix", False)
        if add_prefix:
            prefix = form.get("new-prefix", None)
            if prefix is None:
                await flash(u"No prefix was specified.", "danger")
                return redirect(url_for("dashboard.guild_general", id=id))

            if not is_valid_prefix(prefix):
                await flash(u"That is not a valid prefix.", "danger")
                return redirect(url_for("dashboard.guild_general", id=id))

            result = current_app.db_session.query(CustomPrefixes).filter_by(guild_id=id).first()
            if result is not None:
                prefixes = list(result.prefixes)
                if len(prefixes) == 4:
                    await flash(u"You've hit the prefix limit of four.", "danger")
                    return redirect(url_for("dashboard.guild_general", id=id))

                if any([prefix.startswith(existing_prefix) for existing_prefix in prefixes]):
                    await flash(u"This prefix would conflict with another prefix (this prefix starts with another prefix).", "danger")
                    return redirect(url_for("dashboard.guild_general", id=id))

                if any([existing_prefix.startswith(prefix) for existing_prefix in prefixes]):
                    await flash(u"This prefix would conflict with another prefix (another prefix starts with this prefix).", "danger")
                    return redirect(url_for("dashboard.guild_general", id=id))

                if prefix not in prefixes:
                    prefixes.append(prefix)
                    result.prefixes = prefixes

                    current_app.db_session.commit()

                    if id in current_app.core.bot.prefix_cache:
                        del current_app.core.bot.prefix_cache[id]

                    await flash(u"Added prefix. 🙂👍", "success")
                else:
                    await flash(u"That prefix is already added.", "danger")
            else:
                current_app.db_session.add(CustomPrefixes(guild_id=id, prefixes=[prefix]))
                current_app.db_session.commit()

                if id in current_app.core.bot.prefix_cache:
                    del current_app.core.bot.prefix_cache[id]

                await flash(u"Succesfully set a custom prefix.", "success")

            return redirect(url_for("dashboard.guild_general", id=id))

        return redirect(url_for("dashboard.guild_general", id=id))
    else:
        return "Guild Not Found", 404


@dashboard_bp.route("/guild/<int:id>/notifications/")
@authed_only
async def guild_notifications(id: int):
    user = current_app.user_handler.get_user()
    if id in user.guilds_mapping.keys():
        guild = user.guilds_mapping[id]

        if not guild.user_has_access():
            return "No Permissions"

        setting_channel = None
        selected_setting = request.args.get("setting", None)
        if selected_setting:
            selected_setting = current_app.db_session.query(BNSetting).filter_by(guild_id=id, channel_id=int(selected_setting)).first()
            if selected_setting is None:
                await flash(u"Stream Notifications > That is an invalid notification setting.", "danger")
            else:
                setting_channel = await current_app.core.bot.find_channel(selected_setting.channel_id)

        channels = current_app.core.bot.get_guild(guild.id).channels

        notif_channels = {}
        for i, setting in enumerate(current_app.db_session.query(BNSetting).filter_by(guild_id=id).order_by(BNSetting.id).all()):
            listing_channel = current_app.core.bot.get_channel(setting.channel_id)
            if setting_channel:
                notif_channels[f"#{listing_channel.name} (#{i + 1})"] = setting
            else:
                notif_channels[f"Unknown (#{i + 1})"] = setting

        return await render_template(
            "dashboard/guild_notifications.html",
            guild=guild,

            channels=channels,
            notif_channels=notif_channels,

            selected_setting=selected_setting,
            selected_setting_channel=setting_channel,

            subreddit_filters=current_app.core.rpan_subreddits.list,
        )
    else:
        return redirect(url_for("dashboard.main"))


@dashboard_bp.route("/guild/<int:id>/notifications/submit/", methods=["POST"])
@authed_only
async def guild_notifications_submit(id: int):
    user = current_app.user_handler.get_user()
    if id in user.guilds_mapping.keys():
        guild = user.guilds_mapping[id]

        if not guild.user_has_access():
            return "No Permissions"

        # Fetch the form info.
        await request.get_data()
        form = await request.form

        # Setting up a notification setting.
        if "setup" in form:
            channel_id = form.get("setup_channel", 0)
            if channel_id.isdigit():
                channel_id = int(channel_id)
            else:
                await flash(u"Stream Notifications > That is an invalid channel.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id))

            channel = await current_app.core.bot.find_channel(channel_id)

            # Validate that the channel is real and in the guild.
            valid_channel = False
            if channel is not None:
                if channel.guild.id == id:
                    valid_channel = True

            if not valid_channel:
                await flash(u"Stream Notifications > That is an invalid channel.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id))

            # Check that a setting does not exist already for that channel.
            setting = current_app.db_session.query(BNSetting).filter_by(guild_id=id, channel_id=channel_id).first()
            if setting is not None:
                await flash(u"Stream Notifications > That channel already has a setting. Select it in the other dropdown menu.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id))

            # Setup BN for that channel.
            webhook = await channel.create_webhook(
                name="RPANBot Stream Notifications",
                reason="Notifications setup via web dashboard.",
            )

            setting = BNSetting(
                guild_id=channel.guild.id,
                channel_id=channel.id,
                webhook_url=webhook.url,
            )
            current_app.db_session.add(setting)
            current_app.db_session.commit()

            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={channel_id}")

        # Selecting a notification setting.
        if "select" in form:
            selected_channel = form.get("select_channel", 0)
            if selected_channel.isdigit():
                selected_channel = int(selected_channel)
            else:
                await flash(u"Stream Notifications > That is not a valid notifications channel.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id))

            setting = current_app.db_session.query(BNSetting).filter_by(guild_id=id, channel_id=selected_channel).first()
            if setting is None:
                await flash(u"Stream Notifications > That is not a valid notifications channel.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id))

            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting.channel_id}")

        return redirect(url_for("dashboard.guild_notifications", id=id))
    else:
        return "Guild Not Found", 404


@dashboard_bp.route("/guild/<int:id>/notifications/setting/<int:setting_id>/submit", methods=["POST"])
@authed_only
async def guild_notifications_setting_submit(id: int, setting_id: int):
    user = current_app.user_handler.get_user()
    if id in user.guilds_mapping.keys():
        guild = user.guilds_mapping[id]

        if not guild.user_has_access():
            return "No Permissions"

        # Fetch the form info.
        await request.get_data()
        form = await request.form

        # Get the setting.
        setting = current_app.db_session.query(BNSetting).filter_by(guild_id=id, channel_id=setting_id).first()
        if setting is None:
            await flash(u"Stream Notifications > That is not a valid notifications channel.", "danger")
            return redirect(url_for("dashboard.guild_notifications", id=id))

        # Add a subreddit filter.
        if "add_subreddit" in form:
            subreddit = form.get("subreddit_filter", None)
            if subreddit not in current_app.core.rpan_subreddits.list:
                await flash(u"Subreddit Filters > That is an invalid subreddit.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if setting.subreddit_filters:
                if subreddit in setting.subreddit_filters:
                    await flash(u"Subreddit Filters > That subreddit is already added.", "danger")
                    return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            subreddit_filters = []
            if setting.subreddit_filters is not None:
                subreddit_filters = list(setting.subreddit_filters)
            subreddit_filters.append(subreddit)
            setting.subreddit_filters = subreddit_filters
            current_app.db_session.commit()

            await flash(u"Stream Notifications > Added a subreddit filter.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

        # Add a keyword filter.
        if "add_keyword" in form:
            keyword = form.get("keyword", None)
            if not keyword:
                await flash(u"Keyword Filters > That is an invalid keyword.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if setting.keyword_filters:
                if keyword in setting.keyword_filters:
                    await flash(u"Keyword Filters > That keyword is already added.", "danger")
                    return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

                if len(setting.keyword_filters) >= 25:
                    await flash(u"Keyword Filters > This channel has hit the keyword filter limit of 25.", "danger")
                    return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            keyword_filters = []
            if setting.keyword_filters is not None:
                keyword_filters = list(setting.keyword_filters)
            keyword_filters.append(keyword)
            setting.keyword_filters = keyword_filters
            current_app.db_session.commit()

            await flash(u"Stream Notifications > Added a keyword filter.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

        # Add a user.
        if "add_user" in form:
            username = form.get("username", None)
            if not username:
                await flash(u"Usernames > That is an invalid username.", "warning")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")
            else:
                username = parse_reddit_username(username)

            if not is_valid_reddit_username(username):
                await flash(u"Usernames > That is an invalid Reddit username.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if user.id not in current_app.core.settings.ids.bot_developers:
                if username in ["rpanbot"]:
                    await flash(u"Usernames > That is a disallowed username for stream notifications.", "danger")
                    return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if setting.users.count() >= 50:
                await flash(u"Usernames > This channel is currently at the limit of 50 users.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            user = current_app.db_session.query(BNUser).filter_by(username=username).first()
            if user is None:
                user = BNUser(username=username)
                current_app.db_session.add(user)
            else:
                if setting in user.notifications_for:
                    await flash(u"Usernames > That user is already added to the settings for this channel.", "danger")
                    return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            setting.users.append(user)
            current_app.db_session.commit()

            await flash(u"Usernames > Added a user to the notifications.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

        # Remove a subreddit filter.
        if "remove_subreddit" in form:
            subreddit = form.get("remove_subreddit", None)
            if not subreddit:
                await flash(u"Subreddit Filters > That is an invalid subreddit.", "warning")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if not setting.subreddit_filters or subreddit not in setting.subreddit_filters:
                await flash(u"Subreddit Filters > That is not an added subreddit filter.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            subreddit_filters = list(setting.subreddit_filters)
            subreddit_filters.remove(subreddit)
            setting.subreddit_filters = subreddit_filters
            current_app.db_session.commit()

            await flash(u"Subreddit Filters > Removed a subreddit filter.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

        # Remove a keyword filter.
        if "remove_keyword" in form:
            keyword_index = form.get("remove_keyword", None)
            if not keyword_index:
                await flash(u"Keyword Filters > That is an invalid keyword.", "warning")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")
            else:
                keyword_index = int(keyword_index)

            if not setting.keyword_filters:
                await flash(u"Keyword Filters > There are no keyword filters on this guild.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if keyword_index not in range(0, len(setting.keyword_filters) - 1):
                await flash(u"Keyword Filters > That is not an added keyword filter.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            keyword_filters = list(setting.keyword_filters)
            del keyword_filters[keyword_index]
            setting.keyword_filters = keyword_filters
            current_app.db_session.commit()

            await flash(u"Keyword Filters > Removed a keyword filter.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

        # Remove a user.
        if "remove_user" in form:
            username = form.get("remove_user", None)
            if not username:
                await flash(u"Users > That is an invalid username.", "warning")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if not is_valid_reddit_username(username):
                await flash(u"Users > That is not a valid Reddit username.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            user = current_app.db_session.query(BNUser).filter_by(username=username).first()

            is_valid_removal = True
            if user is None:
                is_valid_removal = False
            elif setting not in user.notifications_for:
                is_valid_removal = False

            if not is_valid_removal:
                await flash(u"Users > That user is not in the settings for this channel.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            setting.users.remove(user)
            current_app.db_session.commit()

            await flash(f"Users > You will no longer receive notifications for u/{username} in this channel.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

        # Setting custom text
        if "set_custom_text" in form:
            custom_text = form.get("custom_text", None)
            if not custom_text:
                setting.custom_text = ""
                current_app.db_session.commit()

                await flash(u"Custom Text > Succesfully removed your custom text.", "success")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            if len(custom_text) > 1000:
                await flash(u"Custom Text > That custom text is beyond the 1000 character limit.", "danger")
                return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

            setting.custom_text = custom_text
            current_app.db_session.commit()

            await flash(u"Custom Text > Succesfully set the custom text.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")

        # Deleting the setting.
        if "delete_setting" in form:
            try:
                async with ClientSession() as session:
                    webhook = Webhook.from_url(setting.webhook_url, adapter=AsyncWebhookAdapter(session))
                    await webhook.delete(reason="Deleted via web panel.")
            except Exception as e:
                print(e)
                pass
            finally:
                current_app.db_session.delete(setting)
                current_app.db_session.commit()

            await flash(f"Stream Notifications > Deleted the notification setting for {setting.channel_id}.", "success")
            return redirect(url_for("dashboard.guild_notifications", id=id))

        return redirect(url_for("dashboard.guild_notifications", id=id) + f"?setting={setting_id}")
    else:
        return "Guild Not Found", 404


@dashboard_bp.app_errorhandler(404)
async def handle_404(err):
    return await render_template("dashboard/404.html"), 404


@dashboard_bp.app_errorhandler(500)
async def handle_500(err):
    return await render_template("dashboard/500.html"), 500
