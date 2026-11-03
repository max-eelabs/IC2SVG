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
    LEGEND_DEFINITION_SCALE, LEGEND_DESCRIPTION_MAX_CHARS,
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


def _truncate_description(
    text: str, maximum_width: float, font: ImageFont.FreeTypeFont, maximum_chars: int
) -> str:
    """Fit one line using an ellipsis when the character or width limit is reached."""
    text = " ".join(text.split())
    if maximum_width <= 0:
        raise ValueError("Category legend cannot fit the selected sheet.")
    if len(text) <= maximum_chars and font.getlength(text) <= maximum_width + 1e-6:
        return text

    prefix = text[:maximum_chars - 3].rstrip()
    while prefix and font.getlength(prefix + "...") > maximum_width + 1e-6:
        prefix = prefix[:-1].rstrip()
    if font.getlength(prefix + "...") > maximum_width + 1e-6:
        raise ValueError("Category legend cannot fit the selected sheet.")
    return prefix + "..."


class TopRightLegendRenderer(LegendRenderer):
    """Draw a top-right block with equal swatches and single-line descriptions.

    Swatches use the injected definition renderer, including active-low overbars.
    The block has a fixed 32-unit sheet margin and its own 50% presentation scale.
    Automatic layout fills columns downward with at most four entries.
    An explicit column count distributes entries evenly and overrides that limit.
    Long descriptions are truncated; a reserved block can keep overlays separate.
    """

    def __init__(
        self, definition_renderer: DefinitionRenderer | None = None, *,
        reserved_bounds: Rectangle | None = None, columns: int | None = None,
        description_max_chars: int = LEGEND_DESCRIPTION_MAX_CHARS,
    ) -> None:
        """Reuse a definition style and optionally avoid an occupied sheet block.

        Args:
            definition_renderer: Swatch style; defaults to rounded colored boxes
                at 90% of the standard definition size.
            columns: Requested columns from 1 through 16, capped by entry count.
                None uses automatic columns with at most four entries each.
            description_max_chars: Maximum displayed description length, including
                the ellipsis. At least four characters; width may trim it further.
                Original entry descriptions are not changed.
            reserved_bounds: Sheet bounds to avoid by moving the legend below
                them. The caller retains ownership; the rectangle is immutable.
        """
        if columns is not None and (type(columns) is not int or not 1 <= columns <= 16):
            raise ValueError("Legend columns must be an integer from 1 to 16 or None.")
        if type(description_max_chars) is not int or description_max_chars < 4:
            raise ValueError(
                "Legend description limit must be an integer of at least 4."
            )
        self._description_max_chars = description_max_chars
        self._columns = columns
        self._reserved_bounds = reserved_bounds
        self._definitions = (
            RoundedDefinitionRenderer(scale=LEGEND_DEFINITION_SCALE)
            if definition_renderer is None else definition_renderer
        )

    def render(
        self, document: SvgDocument, entries: Sequence[LegendEntry]
    ) -> Rectangle:
        """Draw the requested columns without a surrounding box or border.

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
        heading_bounds = document.text_bounds(
            (0, HEADING_POSITION_Y / scale), "Legend",
            font=heading_font, anchor="lm", bold=True,
        )
        heading_height = heading_bounds[3] + HEADING_CONTENT_GAP / scale
        if self._columns is None:
            counts = [min(4, len(entries) - start)
                      for start in range(0, len(entries), 4)]
        else:
            count = min(self._columns, len(entries))
            rows, extra = divmod(len(entries), count)
            counts = [rows + (index < extra) for index in range(count)]
        column_count = len(counts)
        groups = []
        offset = 0
        for count in counts:
            groups.append(entries[offset:offset + count])
            offset += count
        positions = [(column, row) for column, count in enumerate(counts)
                     for row in range(count)]
        available_width = (document.size[0] - 2 * margin) / scale
        column_limit = (available_width - 64 * (column_count - 1)) / column_count
        shortened = [
            _truncate_description(entry.description, float("inf"), description_font,
                                  self._description_max_chars)
            for entry in entries
        ]
        column_widths = [
            min(column_limit, swatch_width + 24 + max(
                description_font.getlength(_truncate_description(
                    entry.description, float("inf"), description_font,
                    self._description_max_chars
                ))
                for entry in group
            ))
            for group in groups
        ]
        descriptions = [
            _truncate_description(
                shortened[index],
                column_widths[positions[index][0]] - swatch_width - 24,
                description_font, self._description_max_chars,
            )
            for index, entry in enumerate(entries)
        ]
        line_height = description_font.size * 1.3
        cell_height = max(swatch_height, line_height)
        row_step = cell_height + 16
        column_starts = [0.0]
        for column_width in column_widths[:-1]:
            column_starts.append(column_starts[-1] + column_width + 64)
        width = max(sum(column_widths) + 64 * (column_count - 1),
                    heading_font.getlength("Legend"))
        height = heading_height + row_step * max(counts) - 16
        left = document.size[0] - margin - width * scale
        block_top = margin
        reserved = self._reserved_bounds
        if reserved is not None and (
            left < reserved.right and document.size[0] - margin > reserved.left
            and block_top < reserved.bottom
            and block_top + height * scale > reserved.top
        ):
            block_top = reserved.bottom + margin
        bottom = block_top + height * scale
        if left < margin - 1e-6 or bottom > document.size[1] - margin:
            raise ValueError("Category legend cannot fit the selected sheet.")

        with document.sheet_layer("legend", position=(left, block_top), scale=scale):
            document.text(
                (0, HEADING_POSITION_Y / scale), "Legend",
                font=heading_font, fill="#333333", anchor="lm",
                bold=True,
            )
            for index, entry in enumerate(entries):
                column, row = positions[index]
                x = column_starts[column]
                cell_top = heading_height + row * row_step
                top = cell_top + (cell_height - swatch_height) / 2
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
                    (x + swatch_width + 24, cell_top + cell_height / 2),
                    descriptions[index], font=description_font,
                    fill="#4B4F55", anchor="lm",
                )
        return Rectangle(left, block_top, document.size[0] - margin, bottom)
