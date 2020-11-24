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

from web.helpers.user_handler import developer_only

from utils.validators import is_valid_reddit_username
from utils.database.models.testing import BNTestingDataset


developer_bp = Blueprint("developer", __name__, url_prefix="/dashboard/developer", template_folder="templates")

@developer_bp.route("/")
@developer_only
async def main():
    return await render_template("developer/main.html")


@developer_bp.route("/dataset/")
@developer_only
async def dataset():
    dataset = current_app.db_session.query(BNTestingDataset).all()
    return await render_template("developer/dataset.html", dataset=dataset)


@developer_bp.route("/dataset/submit/", methods=["POST"])
@developer_only
async def dataset_submit():
    await request.get_data()
    form = await request.form

    # Adding a user.
    if "add_user" in form:
        username = form.get("username", None)

        if not is_valid_reddit_username(username):
            await flash(u"That is an invalid Reddit username.", "danger")
            return redirect(url_for("developer.dataset"))
        else:
            username = username.lower()

        user = current_app.db_session.query(BNTestingDataset).filter_by(username=username).first()
        if user is None:
            user = BNTestingDataset(username=username)
            current_app.db_session.add(user)
            current_app.db_session.commit()
            await flash(u"Added that user.", "success")
        else:
            await flash(u"That user is already added.", "danger")

        return redirect(url_for("developer.dataset"))

    # Removing a user.
    if "remove_user" in form:
        user_id = form.get("remove_user", None)

        if not user_id:
            await flash(u"That is an invalid user id.", "danger")
            return redirect(url_for("developer.dataset"))

        user = current_app.db_session.query(BNTestingDataset).filter_by(id=int(user_id)).first()
        if not user:
            await flash(u"There is no user added with that id", "danger")
            return redirect(url_for("developer.dataset"))

        current_app.db_session.delete(user)
        current_app.db_session.commit()

        await flash(f"Removed u/{user.username}.", "success")
        return redirect(url_for("developer.dataset"))

    return redirect(url_for("developer.dataset"))
