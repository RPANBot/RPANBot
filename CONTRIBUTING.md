# Contributing to RPANBot

First off I'd like to thank you for taking the time to looking into contributing to the bot.

---

### Adding a Feature?

**Requesting a Feature**

To request a feature, please either submit an [issue](https://github.com/RPANBot/RPANBot/issues) on GitHub or let us know in the [Discord guild.](https://discord.gg/DfBp4x4)

**Development Discussion**

We have a channel to discuss the bot's development in the [Discord guild.](https://discord.gg/DfBp4x4)

**Making a Pull Request**

* Open a pull request with your branch.

* Include a description of the new feature/changes.

---

### Found a Bug?

**Reporting the Bug**

If you'd like to report a bug then please submit an [issue](https://github.com/RPANBot/RPANBot/issues) on GitHub or send a message in the [bot's Discord support guild.](https://discord.gg/DfBp4x4)

**Written a patch for the bug?**

Thank you for taking the time to make a code contribution to RPANBot.

* Open a pull request with the patch.

* Please include a description that describes the issue and solution that you used to solve it.

---

### Setting up a development environment.

RPANBot utilises [Docker](https://www.docker.com/) and [docker-compose](https://github.com/docker/compose) for running the bot and [PostgreSQL](https://www.postgresql.org/) containers.

Here's a guide to setting up your environment:

* Make a copy of ``configs/config.yml.example`` and rename it to ``configs/config.yml``
    * Add your testing guild(s) to the ``rpan_guilds`` section.
    * Add your [Discord ID](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID) to the ``bot_developer_ids`` section.
    * Change the channel IDs in the ``channels`` section.


* Make a copy of ``configs/bot.env.example`` and rename it to ``configs/bot.env``
    * Add your [Discord application's](https://discord.com/developers/applications) client id and secret to ``DISCORD_CLIENT_ID`` and ``DISCORD_CLIENT_SECRET``.
    * Create a [Reddit application](https://old.reddit.com/prefs/apps/) and add your client id and secret to ``REDDIT_CLIENT_ID`` and ``REDDIT_CLIENT_SECRET``
        * Generate a [refresh token](https://praw.readthedocs.io/en/latest/tutorials/refresh_token.html) and add it to ``REDDIT_REFRESH_TOKEN``
    * You can also utilise [Sentry error tracking](https://docs.sentry.io/product/sentry-basics/guides/integrate-frontend/create-new-project/) and add a link under ``SENTRY_LINK``, but this is optional.


* Start the bot by running ``docker-compose up -f rpanbot_docker/docker-compose.dev.yml`` from the main directory.

---

### Contributor Discussion

Contributors can communicate using:
* GitHub [issues](https://github.com/RPANBot/RPANBot/issues) and comments on them.
* The development discussion channels in the [Discord support guild.](https://discord.gg/DfBp4x4)

Please note that these channels do not provide support for self hosting, only for contributing to or developing the bot.
