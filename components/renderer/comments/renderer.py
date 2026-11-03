# Copyright 2026 Maxim Pavlov <pavlov.web@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

"""Replaceable comments blocks placed independently of the IC drawing."""

from abc import ABC, abstractmethod
from collections.abc import Sequence

from PIL import ImageFont

from ..core import Rectangle, SvgDocument
from ..core.typography import (
    HEADING_CONTENT_GAP, HEADING_FONT_SIZE, HEADING_POSITION_Y,
    OVERLAY_FONT_SIZE, OVERLAY_ROW_HEIGHT,
)


def _wrap_line(text: str, width: float, font: ImageFont.FreeTypeFont) -> list[str]:
    """Wrap by actual font advances, including words longer than a full line."""
    lines = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if font.getlength(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        for character in word:
            if current and font.getlength(current + character) > width:
                lines.append(current)
                current = ""
            current += character
    if current:
        lines.append(current)
    return lines or [""]


class CommentsRenderer(ABC):
    """Draw comments in sheet coordinates and report the occupied bounds."""

    @abstractmethod
    def render(self, document: SvgDocument, comments: Sequence[str]) -> Rectangle:
        """Draw the supplied comments, preserving their order."""


class BottomLeftCommentsRenderer(CommentsRenderer):
    """Draw a borderless, left-aligned block 32 units from the sheet's edges.

    Font sizes and margins are sheet units, independent of chip content scaling.
    Long comments wrap to a maximum width of 1120 units or the available sheet.
    """

    def render(self, document: SvgDocument, comments: Sequence[str]) -> Rectangle:
        """Wrap comments above the bottom margin, raising if they cannot fit."""
        margin = 32.0
        bottom = document.size[1] - margin
        if not comments:
            return Rectangle(margin, bottom, margin, bottom)
        if any(not isinstance(text, str) or not text.strip() for text in comments):
            raise ValueError("Each comment must be a nonempty string.")

        font = ImageFont.load_default(size=OVERLAY_FONT_SIZE)
        width = min(1120, document.size[0] - 2 * margin)
        lines = [
            line
            for comment in comments
            for paragraph in comment.splitlines()
            for line in _wrap_line(paragraph, width, font)
        ]
        row_height = OVERLAY_ROW_HEIGHT
        heading_font = ImageFont.load_default(size=HEADING_FONT_SIZE)
        heading_bounds = document.text_bounds(
            (0, HEADING_POSITION_Y), "Comments",
            font=heading_font, anchor="lm", bold=True,
        )
        first_index = next(index for index, line in enumerate(lines) if line)
        first_line_bounds = document.text_bounds(
            (0, (first_index + 0.5) * row_height), lines[first_index],
            font=font, anchor="lm",
        )
        heading_height = (
            heading_bounds[3] + HEADING_CONTENT_GAP + 8 - first_line_bounds[1]
        )
        height = heading_height + len(lines) * row_height
        top = bottom - height
        if top < margin:
            raise ValueError("Comments block cannot fit the selected sheet.")

        with document.sheet_layer("comments"):
            document.text(
                (margin, top + HEADING_POSITION_Y), "Comments",
                font=heading_font,
                fill="#333333", anchor="lm", bold=True,
            )
            for index, line in enumerate(lines):
                if not line:
                    continue
                document.text(
                    (margin, top + heading_height + (index + 0.5) * row_height),
                    line, font=font, fill="#4B4F55", anchor="lm",
                )
        actual_width = max(font.getlength(line) for line in lines)
        actual_width = max(actual_width, ImageFont.load_default(size=HEADING_FONT_SIZE)
                           .getlength("Comments"))
        return Rectangle(margin, top, margin + actual_width, bottom)
