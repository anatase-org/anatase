#!/usr/bin/env python3

import json
import re
import sys
from html.parser import HTMLParser


DISCORD_TITLE_LIMIT = 256
DISCORD_DESCRIPTION_LIMIT = 4096


def truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


class UpdateParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.meta_title = ""
        self.meta_description = ""
        self.paragraphs: list[str] = []
        self._in_title = False
        self._body_depth = 0
        self._paragraph_depth = 0
        self._title_parts: list[str] = []
        self._paragraph_parts: list[str] = []
        self._intro_finished = False

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name")
            content = attributes.get("content", "")
            if key == "og:title":
                self.meta_title = content
            elif key == "og:description":
                self.meta_description = content

        if tag == "h1" and not self.title:
            self._in_title = True

        if tag == "div":
            if attributes.get("id") == "__blog-post-container":
                self._body_depth = 1
            elif self._body_depth:
                self._body_depth += 1

        if self._body_depth and not self._intro_finished and tag == "p":
            self._paragraph_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1" and self._in_title:
            self.title = normalize("".join(self._title_parts))
            self._in_title = False

        if self._paragraph_depth and tag == "p":
            self._paragraph_depth -= 1
            if not self._paragraph_depth:
                paragraph = normalize("".join(self._paragraph_parts))
                if paragraph:
                    self.paragraphs.append(paragraph)
                self._paragraph_parts.clear()

        if self._body_depth and tag == "div":
            self._body_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_parts.append(data)
        if self._paragraph_depth and not self._intro_finished:
            self._paragraph_parts.append(data)

    def handle_comment(self, data: str) -> None:
        if self._body_depth and data.strip() in ("", "truncate"):
            self._intro_finished = True

    def summary(self) -> dict[str, str]:
        title = self.title or self.meta_title
        description = "\n\n".join(self.paragraphs) or self.meta_description
        return {
            "title": truncate(title, DISCORD_TITLE_LIMIT),
            "description": truncate(description, DISCORD_DESCRIPTION_LIMIT),
        }


def main() -> None:
    parser = UpdateParser()
    parser.feed(sys.stdin.read())
    print(json.dumps(parser.summary(), ensure_ascii=False))


if __name__ == "__main__":
    main()
