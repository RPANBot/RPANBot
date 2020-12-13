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
from typing import Union


class RPANSubreddits:
    def __init__(self) -> None:
        # Hardcoded RPAN Community Subreddits
        self.list = [
            "pan",
            "animalsonreddit",
            "distantsocializing",
            "glamourschool",
            "headlineworthy",
            "lgbt",
            "readwithme",
            "redditinthekitchen",
            "redditmasterclasses",
            "redditsessions",
            "shortcircuit",
            "talentshow",
            "theartiststudio",
            "thegamerlounge",
            "theyoushow",
            "whereintheworld"
        ]

        self.abbreviations = {
            "aor": "animalsonreddit",
            "ds": "distantsocializing",
            "gs": "glamourschool",
            "hw": "headlineworthy",
            "rwm": "readwithme",
            "ritk": "redditinthekitchen",
            "rmc": "redditmasterclasses",
            "rs": "redditsessions",
            "sc": "shortcircuit",
            "ts": "talentshow",
            "tas": "theartiststudio",
            "tgl": "thegamerlounge",
            "tys": "theyoushow",
            "witw": "whereintheworld"
        }

    def ref_to_full(self, reference: str) -> Union[str, None]:
        """
        A subreddit reference name to the full subreddit name.
        :return: The full subreddit name or None if not found.
        """
        reference = reference.lower()
        if reference in self.list:
            return reference

        if reference in self.abbreviations.keys():
            return self.abbreviations[reference]

        return None
