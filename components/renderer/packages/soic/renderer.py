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

"""Render SOIC housings and gull-wing leads from package-owned variant data."""

from PIL import ImageFont

from ...core import (
    IcRenderer, Orientation, PackageDimension, PackageLayout, Pin, Rectangle,
    SvgDocument,
)
from ...core.typography import LABEL_FONT_SIZE, PIN_NUMBER_GAP
from .catalog import SOIC_VARIANTS


_VARIANTS = {variant.pin_count: variant for variant in SOIC_VARIANTS}
SUPPORTED_PIN_COUNTS = tuple(sorted(_VARIANTS))

# Fixed logical magnification; identical physical dimensions share one scale.
_UNITS_PER_MM = 90.0


class SoicRenderer(IcRenderer):
    """Draw narrow-body SOIC packages viewed from above, with pin 1 upper left.

    Physical numbering runs down the left side and up the right. Dimensions
    describe the plastic body and metal leads, not solder lands. Decorative
    bevels, bend shading, and the pin-one dot are illustrative. Wide-body SOIC
    and packages with exposed pads require separate variants.
    """

    def __init__(self, pin_count: int = 8) -> None:
        """Select a supported physical lead count before constructing a layout."""
        if type(pin_count) is not int or pin_count not in _VARIANTS:
            supported = ", ".join(str(count) for count in SUPPORTED_PIN_COUNTS)
            raise ValueError(f"Unsupported SOIC pin count. Supported: {supported}.")

        self._variant = _VARIANTS[pin_count]

    @property
    def pin_count(self) -> int:
        """Return the number of physical leads."""
        return self._variant.pin_count

    @property
    def reference_dimensions(self) -> tuple[PackageDimension, ...]:
        """Return fixed reference ranges in body width, length, span, pitch order."""
        specification = self._variant.specification
        return tuple(
            PackageDimension(label, value.inches, value.millimeters)
            for label, value in (
                ("Body width", specification.body_width),
                ("Body length", specification.body_length),
                ("Lead span", specification.lead_span),
                ("Pin pitch", specification.pin_pitch),
            )
        )

    @property
    def nominal_dimensions_mm(self) -> tuple[float, float, float, float]:
        """Return illustrative body width, length, overall lead span, and pitch.

        Geometry uses nominal values. Reference ranges remain
        separate and retain manufacturing tolerances.
        """
        geometry = self._variant.geometry
        return geometry.width, geometry.length, geometry.span, geometry.pitch

    def package_layout(self, orientation: Orientation) -> PackageLayout:
        """Center the body and leads without changing their physical proportions."""
        if not isinstance(orientation, Orientation):
            raise TypeError("Orientation must be an Orientation enum member.")

        cx, cy = (value / 2 for value in orientation.value)
        geometry = self._variant.geometry
        units = _UNITS_PER_MM
        half_width = geometry.width * units / 2
        half_length = geometry.length * units / 2
        half_span = geometry.span * units / 2
        half_lead = geometry.lead_width * units / 2
        body = Rectangle(
            cx - half_width, cy - half_length, cx + half_width, cy + half_length
        )
        pins = []
        rows = self.pin_count // 2
        for number in range(1, self.pin_count + 1):
            is_left = number <= rows
            row = number - 1 if is_left else self.pin_count - number
            y = cy + (row - (rows - 1) / 2) * geometry.pitch * units
            left = cx - half_span if is_left else body.right
            right = body.left if is_left else cx + half_span
            bounds = Rectangle(left, y - half_lead, right, y + half_lead)
            pins.append(Pin(number, bounds))
        return PackageLayout(body, tuple(pins))

    @staticmethod
    def _number_position(
        pin: Pin, layout: PackageLayout, font: ImageFont.FreeTypeFont
    ) -> tuple[float, float]:
        is_left = pin.bounds.right <= layout.body.left
        y = (pin.bounds.top + pin.bounds.bottom) / 2
        anchor = "rm" if is_left else "lm"
        bounds = SvgDocument.text_bounds(
            (0, y), str(pin.number), font=font, anchor=anchor, bold=True
        )
        if is_left:
            return pin.bounds.left - PIN_NUMBER_GAP - bounds[2], y
        return pin.bounds.right + PIN_NUMBER_GAP - bounds[0], y

    def pin_number_bounds(self, pin: Pin, layout: PackageLayout) -> Rectangle:
        """Return visible glyph bounds used by the shared annotation compositor."""
        font = ImageFont.load_default(size=LABEL_FONT_SIZE)
        return Rectangle(*SvgDocument.text_bounds(
            self._number_position(pin, layout, font), str(pin.number), font=font,
            anchor="rm" if pin.bounds.right <= layout.body.left else "lm",
            bold=True,
        ))

    def render_pins(self, draw: SvgDocument, layout: PackageLayout) -> None:
        """Draw metal leads with bend shading, then their physical numbers."""
        font = ImageFont.load_default(size=LABEL_FONT_SIZE)
        for pin in layout.pins:
            bounds = pin.bounds
            draw.polygon(
                [(bounds.left, bounds.top), (bounds.right, bounds.top),
                 (bounds.right, bounds.bottom), (bounds.left, bounds.bottom)],
                fill="#A6ABB0", outline="#646A70", width=2,
            )
            bend = (bounds.left + bounds.right) / 2
            draw.line(
                (bend, bounds.top + 2, bend, bounds.bottom - 2),
                fill="#E4E7EA", width=5,
            )
            draw.text(
                self._number_position(pin, layout, font), str(pin.number),
                font=font, fill="#333333", bold=True,
                anchor="rm" if bounds.right <= layout.body.left else "lm",
            )

    def render_package(
        self, draw: SvgDocument, layout: PackageLayout, ic_name: str
    ) -> None:
        """Draw the beveled plastic body, orientation dot, and fitted name."""
        body = layout.body
        cx = (body.left + body.right) / 2
        cy = (body.top + body.bottom) / 2
        font = self._name_font(ic_name, body.right - body.left - 40)
        draw.rounded_rectangle(
            body.box, radius=12, fill="#202226", outline="#151619", width=3,
        )
        draw.rounded_rectangle(
            (body.left + 10, body.top + 10, body.right - 10, body.bottom - 10),
            radius=8, fill="#33363B", outline="#4B4F55", width=2,
        )
        draw.ellipse(
            (body.left + 42, body.top + 42, body.left + 99, body.top + 99),
            fill="#202226", outline="#656A71", width=2,
        )
        draw.text((cx, cy), ic_name, font=font, fill="#F2F2F2", anchor="mm")
        draw.text(
            (cx, body.bottom - 42), f"SOIC-{self.pin_count}",
            font=ImageFont.load_default(size=30), fill="#A6ABB0", anchor="mm",
        )

    @staticmethod
    def _name_font(name: str, available_width: float) -> ImageFont.FreeTypeFont:
        # The embedded font keeps glyph measurements and outlines reproducible.
        for size in range(56, 17, -1):
            font = ImageFont.load_default(size=size)
            if font.getlength(name) <= available_width:
                return font
        raise ValueError("IC name is too long to fit the SOIC housing legibly.")
