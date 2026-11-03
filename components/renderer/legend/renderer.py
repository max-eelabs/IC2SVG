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

"""Independent legend strategies composed from existing definition renderers."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from PIL import ImageFont

from ..core import Rectangle, SvgDocument
from ..core.typography import (
    HEADING_CONTENT_GAP, HEADING_FONT_SIZE, HEADING_POSITION_Y,
    LEGEND_SCALE, OVERLAY_FONT_SIZE,
)
from ..definition import DefinitionRenderer, PinLabel, RoundedDefinitionRenderer


@dataclass(frozen=True)
class LegendEntry:
    """A representative colored definition and its category description."""

    sample: PinLabel
    description: str
    variants: tuple[PinLabel, ...] = ()

    @property
    def swatch(self) -> PinLabel:
        """Combine variant names into one box while retaining the primary style."""
        if not self.variants:
            return self.sample
        return PinLabel(
            "/".join(label.text for label in (self.sample, *self.variants)),
            self.sample.color, self.sample.text_color,
        )


class LegendRenderer(ABC):
    """Draw a category key in sheet coordinates, independent of chip scaling."""

    @abstractmethod
    def render(
        self, document: SvgDocument, entries: Sequence[LegendEntry]
    ) -> Rectangle:
        """Draw the supplied entries and return the occupied bounds on the sheet."""


class TopRightLegendRenderer(LegendRenderer):
    """Draw a borderless top-right block with equal swatches and descriptions.

    Swatches use the injected definition renderer, including active-low overbars.
    The block has a fixed 32-unit sheet margin and its own 50% presentation scale.
    Columns fill downward with at most four entries, then continue to the right.
    """

    def __init__(self, definition_renderer: DefinitionRenderer | None = None) -> None:
        """Reuse a definition style; default to the existing rounded colored boxes."""
        self._definitions = (
            RoundedDefinitionRenderer()
            if definition_renderer is None else definition_renderer
        )

    def render(
        self, document: SvgDocument, entries: Sequence[LegendEntry]
    ) -> Rectangle:
        """Draw up to four rows per column without a surrounding box or border.

        Raises:
            ValueError: The complete legend cannot fit on the sheet.
        """
        margin = 32.0
        scale = LEGEND_SCALE
        if not entries:
            return Rectangle(document.size[0] - margin, margin,
                             document.size[0] - margin, margin)

        sizes = [self._definitions.measure(entry.swatch) for entry in entries]
        swatch_width = max(size.width for size in sizes)
        swatch_height = max(size.height for size in sizes)
        description_font = ImageFont.load_default(size=OVERLAY_FONT_SIZE / scale)
        heading_font = ImageFont.load_default(size=HEADING_FONT_SIZE / scale)
        description_width = max(
            description_font.getlength(entry.description) for entry in entries
        )
        row_step = swatch_height + 16
        heading_bounds = document.text_bounds(
            (0, HEADING_POSITION_Y / scale), "Legend",
            font=heading_font, anchor="lm", bold=True,
        )
        heading_height = heading_bounds[3] + HEADING_CONTENT_GAP / scale
        max_rows = 4
        column_count = (len(entries) + max_rows - 1) // max_rows
        column_width = swatch_width + 24 + description_width
        column_step = column_width + 64
        width = max(column_step * column_count - 64,
                    heading_font.getlength("Legend"))
        height = heading_height + row_step * min(len(entries), max_rows) - 16
        left = document.size[0] - margin - width * scale
        bottom = margin + height * scale
        if left < margin or bottom > document.size[1] - margin:
            raise ValueError("Category legend cannot fit the selected sheet.")

        with document.sheet_layer("legend", position=(left, margin), scale=scale):
            document.text(
                (0, HEADING_POSITION_Y / scale), "Legend",
                font=heading_font, fill="#333333", anchor="lm",
                bold=True,
            )
            for index, entry in enumerate(entries):
                column, row = divmod(index, max_rows)
                x = column * column_step
                top = heading_height + row * row_step
                box = Rectangle(x, top, x + swatch_width, top + swatch_height)
                if entry.variants:
                    colors = tuple(
                        label.color for label in (entry.sample, *entry.variants)
                    )
                    with document.override_fill(entry.sample.color,
                                                document.split_fill(colors, box.box)):
                        self._definitions.render(document, entry.swatch, box)
                else:
                    self._definitions.render(document, entry.sample, box)
                document.text(
                    (x + swatch_width + 24, top + swatch_height / 2), entry.description,
                    font=description_font, fill="#4B4F55", anchor="lm",
                )
        return Rectangle(left, margin, document.size[0] - margin, bottom)
