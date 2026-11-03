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

"""Sheet-anchored reference measurements with standard overlay typography."""

from PIL import ImageFont

from .core import IcRenderer, Rectangle, SvgDocument
from .core.typography import (
    HEADING_CONTENT_GAP, HEADING_FONT_SIZE, HEADING_POSITION_Y,
    OVERLAY_FONT_SIZE, OVERLAY_ROW_HEIGHT,
)


class TopLeftPackageRenderer:
    """Draw published package measurements independently of chip content scaling."""

    def render(self, document: SvgDocument, package: IcRenderer) -> Rectangle:
        """Draw a top-left block and return its bounds in logical sheet units.

        Measurements come from the selected package's fixed reference rows,
        with inches first and millimeters in parentheses. Source rounding and ranges are
        retained independently of illustrative geometry changes.
        The heading matches Legend's size, vertical position, and visible gap.

        Raises:
            ValueError: The block cannot fit within the sheet margins.
        """
        margin = 32.0
        measurements = package.reference_dimensions
        if not measurements:
            raise ValueError("Package renderer must provide reference dimensions.")
        lines = tuple(
            f"{value.label}: {value.inches} in ({value.millimeters} mm)"
            for value in measurements
        )
        heading_font = ImageFont.load_default(size=HEADING_FONT_SIZE)
        font = ImageFont.load_default(size=OVERLAY_FONT_SIZE)
        heading_y = HEADING_POSITION_Y
        heading_bounds = document.text_bounds(
            (0, heading_y), "Package", font=heading_font, anchor="lm", bold=True,
        )
        first_bounds = document.text_bounds(
            (0, 0), lines[0], font=font, anchor="lm",
        )
        first_y = heading_bounds[3] + HEADING_CONTENT_GAP - first_bounds[1]
        row_step = OVERLAY_ROW_HEIGHT
        line_bounds = [
            document.text_bounds(
                (0, first_y + index * row_step), line, font=font, anchor="lm",
            )
            for index, line in enumerate(lines)
        ]
        right = margin + max(heading_bounds[2], *(b[2] for b in line_bounds))
        bottom = margin + line_bounds[-1][3]
        if right > document.size[0] - margin or bottom > document.size[1] - margin:
            raise ValueError("Package measurements cannot fit the selected sheet.")

        with document.sheet_layer("package-info", position=(margin, margin)):
            document.text(
                (0, heading_y), "Package", font=heading_font, fill="#333333",
                anchor="lm", bold=True,
            )
            for index, line in enumerate(lines):
                document.text(
                    (0, first_y + index * row_step), line, font=font,
                    fill="#4B4F55", anchor="lm",
                )
        return Rectangle(margin, margin, right, bottom)
