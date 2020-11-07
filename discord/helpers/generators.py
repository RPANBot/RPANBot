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
from discord import Colour, Embed, Message

from typing import Union


class RPANEmbed(Embed):
    def __init__(
        self,

        title: str,
        description: str = "",
        url: str = "",

        colour: Union[int, Colour] = 0x00688B,

        fields: dict = None,
        thumbnail: str = None,

        user=None,
        footer_text: str = None,

        bot=None,
        message: Message = None,
    ) -> None:
        """
        Generates a standard bot embed.

        :param title: The embed's title.
        :param description: The embed's description.
        :param url: The URL permalink used in the title.

        :param colour: The colour of the embed.

        :param fields: The embed's fields (given as a dict).
        :param thumbnail: The thumbnail that the embed should use.

        :param user: The user who has requested a command (if any).
        :param footer_text: Text that should be used in the embed's footer.

        :param bot: The bot instance. This is used to get the custom prefix.
        :param message: The message. This is used to get the custom prefix.

        :return: An embed generated to the specifications.
        """
        if fields is None:
            fields = {}

        if not isinstance(colour, Colour):
            colour = Colour(colour)

        super().__init__(
            title=title,
            description=description,
            url=url,
            colour=colour,
        )

        for key, value in fields.items():
            self.add_field(name=key, value=value)

        if thumbnail:
            self.set_thumbnail(url=thumbnail)

        if user:
            requested_by_text = f"Requested by {user}"
            if footer_text:
                footer_text = requested_by_text + " ● " + footer_text
            else:
                footer_text = requested_by_text

        if footer_text:
            if message:
                self.set_footer(text=f"{footer_text} ● rpanbot.botcavern.xyz")
            else:
                self.set_footer(text=footer_text)
        else:
            if message:
                self.set_footer(text="More Info: rpanbot.botcavern.xyz")
