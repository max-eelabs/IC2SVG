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

"""Independent test geometry, deliberately unrelated to the DIP implementation."""

from collections.abc import Mapping, Sequence

from PIL import ImageFont

from components.renderer.core import (
    IcRenderer, Orientation, PackageDimension, PackageLayout, Pin, Rectangle,
    SvgDocument,
)
from components.renderer.definition import PinDefinition, PinLabel
from components.renderer.pinout import PinoutRenderer, PinType


class AddonRenderer(IcRenderer):
    """Provide a small and a large synthetic package for extension tests."""

    def __init__(self, pin_count: int) -> None:
        self._pin_count = pin_count

    @property
    def pin_count(self) -> int:
        """Return this synthetic variant's physical pin count."""
        return self._pin_count

    @property
    def reference_dimensions(self) -> tuple[PackageDimension, ...]:
        """Supply package-owned rows that the generic overlay must preserve."""
        return (PackageDimension("Test pitch", "0.100", "2.54"),)

    def package_layout(self, orientation: Orientation) -> PackageLayout:
        """Place two rows of numbered pins in logical sheet coordinates."""
        width, height = orientation.value
        cx, cy = width / 2, height / 2
        rows = self.pin_count // 2
        body = Rectangle(cx - 100, cy - rows * 26, cx + 100, cy + rows * 26)
        pins = []
        for number in range(1, self.pin_count + 1):
            is_left = number <= rows
            row = number - 1 if is_left else self.pin_count - number
            y = cy + (row - (rows - 1) / 2) * 52
            left = body.left - 24 if is_left else body.right
            pins.append(Pin(number, Rectangle(left, y - 8, left + 24, y + 8)))
        return PackageLayout(body, tuple(pins))

    def pin_number_bounds(self, pin: Pin, layout: PackageLayout) -> Rectangle:
        """Measure physical numbers with the same fixed font used to draw them."""
        is_left = pin.number <= self.pin_count // 2
        x = pin.bounds.left - 28 if is_left else pin.bounds.right + 28
        y = (pin.bounds.top + pin.bounds.bottom) / 2
        return Rectangle(*SvgDocument.text_bounds(
            (x, y), str(pin.number), font=ImageFont.load_default(size=20),
            anchor="rm" if is_left else "lm",
        ))

    def render_pins(self, draw: SvgDocument, layout: PackageLayout) -> None:
        """Draw all metal footprints and physical numbers in numeric order."""
        for pin in layout.pins:
            draw.rounded_rectangle(
                pin.bounds.box, radius=1, fill="#AAAAAA", outline="#555555", width=1,
            )
            is_left = pin.number <= self.pin_count // 2
            x = pin.bounds.left - 28 if is_left else pin.bounds.right + 28
            y = (pin.bounds.top + pin.bounds.bottom) / 2
            draw.text(
                (x, y), str(pin.number), font=ImageFont.load_default(size=20),
                fill="#333333", anchor="rm" if is_left else "lm",
            )

    def render_package(
        self, draw: SvgDocument, layout: PackageLayout, ic_name: str
    ) -> None:
        """Draw a simple synthetic housing with the requested name."""
        draw.rounded_rectangle(
            layout.body.box, radius=4, fill="#333333", outline="#222222", width=1,
        )
        draw.text(
            ((layout.body.left + layout.body.right) / 2,
             (layout.body.top + layout.body.bottom) / 2),
            ic_name, font=ImageFont.load_default(size=20), fill="#FFFFFF", anchor="mm",
        )


class AddonPinoutRenderer(PinoutRenderer):
    """Exercise package-owned annotation strategies without changing the loader."""

    def render(
        self,
        ic_name: str,
        labels: Mapping[int, PinLabel | Sequence[PinDefinition]] | None = None,
        orientation: Orientation = Orientation.LANDSCAPE,
        *,
        content_scale: float = 0.6,
        pin_types: Mapping[int, PinType] | None = None,
    ) -> SvgDocument:
        """Delegate this two-row layout and mark the chosen plugin strategy."""
        document = super().render(
            ic_name, labels, orientation,
            content_scale=content_scale, pin_types=pin_types,
        )
        with document.sheet_layer("addon-pinout"):
            document.text(
                (32, 160), "Addon strategy", font=ImageFont.load_default(size=14),
                fill="#555555", anchor="lm",
            )
        return document
