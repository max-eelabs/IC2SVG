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

"""Shared top-view housing and pin rendering rules for supported DIP packages."""

from PIL import ImageFont

from ...core import (
    IcRenderer, Orientation, PackageDimension, PackageLayout, Pin, Rectangle,
    SvgDocument,
)
from ...core.typography import LABEL_FONT_SIZE, PIN_NUMBER_GAP
from .catalog import DIP_VARIANTS
from .specifications import dip_specification


_UNITS_PER_MM = 65.0

# Visual clearance beyond the entire end-pin shoulder, not just its center.
_MIN_END_CLEARANCE_MM = 0.75

# Remove length only from the original broad shoulder; retain the taper and tip.
_ORIGINAL_WIDE_RATIO = 0.55
_SHORT_WIDE_RATIO = 0.315


# DIP-4: Diodes DIP-4 outline; DIP-6: Vishay 83253 (existing proportions).
# Others: Microchip DS00049W, printed pages 32–37 and 39, nominal dimensions.
# DIP-16 uses the 19.30 mm body envelope listed for TI's N package.
# https://www.diodes.com/assets/Package-Files/DIP-4.pdf
# https://www.vishay.com/docs/83253/83253.pdf
# https://ww1.microchip.com/downloads/en/PackagingSpec/00049w.pdf
# https://www.ti.com/packaging/tw/docs/searchtipackages.tsp?packageName=DIP
# DIP-24 is the wide 600-mil variant; DIP-28 is the narrow 300-mil variant.
_DIMENSIONS = {variant.pin_count: variant.geometry for variant in DIP_VARIANTS}

# Keep sample generation and callers in sync with the actual geometry registry.
SUPPORTED_PIN_COUNTS = tuple(sorted(_DIMENSIONS))


class DipRenderer(IcRenderer):
    """Render DIP packages with a shared plastic body, notch, and pin-one dot.

    Pin one is at the upper left. Numbers run down the left side and then up
    the right side. All sizes share the same rendering implementation. Nominal
    dimensions omit manufacturing tolerances; decorative detail is illustrative.
    """

    def __init__(self, pin_count: int = 6) -> None:
        """Select a supported total pin count; the default remains DIP-6."""
        if type(pin_count) is not int or pin_count not in _DIMENSIONS:
            supported = ", ".join(str(count) for count in _DIMENSIONS)
            raise ValueError(f"Unsupported DIP pin count. Supported: {supported}.")

        self._pin_count = pin_count
        self._dimensions = _DIMENSIONS[pin_count]

    @property
    def pin_count(self) -> int:
        """Return the total physical pin count."""
        return self._pin_count

    @property
    def reference_dimensions(self) -> tuple[PackageDimension, ...]:
        """Return the fixed reference table rows for the selected DIP pin count."""
        specification = dip_specification(self.pin_count)
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
        """Return body width, body length, lead span, and pin pitch in mm.

        Values describe the nominal package before illustrative lead shortening
        or body enlargement for pin clearance; manufacturing tolerances are omitted.
        """
        return (
            self._dimensions.width, self._dimensions.length,
            self._dimensions.span, self._dimensions.pitch,
        )

    def _units_per_mm(self, orientation: Orientation) -> float:
        width, height = orientation.value
        return min(
            _UNITS_PER_MM,
            (height - 160) / self._body_length_mm(),
            (width - 200) / self._rendered_span_mm(),
        )

    def _rendered_span_mm(self) -> float:
        original_length = (self._dimensions.span - self._dimensions.width) / 2
        shortened_length = original_length * (
            1 - _ORIGINAL_WIDE_RATIO + _SHORT_WIDE_RATIO
        )
        return self._dimensions.width + 2 * shortened_length

    def _body_length_mm(self) -> float:
        pin_envelope = (
            (self.pin_count // 2 - 1) * self._dimensions.pitch
            + self._dimensions.shoulder
        )
        return max(
            self._dimensions.length, pin_envelope + 2 * _MIN_END_CLEARANCE_MM
        )

    def _detail_scale(self, layout: PackageLayout) -> float:
        return (
            (layout.body.right - layout.body.left)
            / self._dimensions.width
            / _UNITS_PER_MM
        )

    def package_layout(self, orientation: Orientation) -> PackageLayout:
        """Center the selected package, uniformly reducing it to fit if needed."""
        width, height = orientation.value
        cx, cy = width / 2, height / 2
        units = self._units_per_mm(orientation)
        half_width = self._dimensions.width * units / 2
        half_length = self._body_length_mm() * units / 2
        half_span = self._rendered_span_mm() * units / 2
        half_shoulder = self._dimensions.shoulder * units / 2
        body = Rectangle(
            cx - half_width, cy - half_length, cx + half_width, cy + half_length
        )
        pins = []

        rows = self.pin_count // 2
        for number in range(1, self.pin_count + 1):
            is_left = number <= rows
            row = number - 1 if is_left else self.pin_count - number
            y = cy + (row - (rows - 1) / 2) * self._dimensions.pitch * units
            left = cx - half_span if is_left else body.right
            right = body.left if is_left else cx + half_span
            bounds = Rectangle(left, y - half_shoulder, right, y + half_shoulder)
            pins.append(Pin(number, bounds))

        return PackageLayout(body, tuple(pins))

    def render_pins(self, draw: SvgDocument, layout: PackageLayout) -> None:
        """Draw short lead shoulders tapering to tips, with physical numbers."""
        scale = self._detail_scale(layout)
        units = _UNITS_PER_MM * scale
        font = ImageFont.load_default(size=LABEL_FONT_SIZE)

        for pin in layout.pins:
            bounds = pin.bounds
            is_left = pin.number <= self.pin_count // 2
            y = (bounds.top + bounds.bottom) / 2
            root = bounds.right if is_left else bounds.left
            tip = bounds.left if is_left else bounds.right
            direction = -1 if is_left else 1
            original_length = (
                (self._dimensions.span - self._dimensions.width) * units / 2
            )
            shoulder = root + direction * original_length * _SHORT_WIDE_RATIO
            taper_end = tip - direction * 0.20 * units
            half_tip = self._dimensions.tip * units / 2
            draw.polygon(
                [
                    (root, bounds.top),
                    (shoulder, bounds.top),
                    (taper_end, y - half_tip),
                    (tip, y - half_tip),
                    (tip, y + half_tip),
                    (taper_end, y + half_tip),
                    (shoulder, bounds.bottom),
                    (root, bounds.bottom),
                ],
                fill="#A6ABB0",
                outline="#646A70",
                width=2 * scale,
            )
            draw.line(
                (root, bounds.top + 8 * scale, shoulder, bounds.top + 8 * scale),
                fill="#E4E7EA",
                width=5 * scale,
            )
            x, y = self._number_position(pin, layout, font)
            draw.text(
                (x, y),
                str(pin.number),
                font=font,
                fill="#333333",
                anchor="rm" if is_left else "lm",
                bold=True,
            )

    def _number_position(
        self, pin: Pin, layout: PackageLayout, font: ImageFont.FreeTypeFont
    ) -> tuple[float, float]:
        is_left = pin.number <= self.pin_count // 2
        y = (pin.bounds.top + pin.bounds.bottom) / 2
        anchor = "rm" if is_left else "lm"
        bounds = SvgDocument.text_bounds(
            (0, y), str(pin.number), font=font, anchor=anchor, bold=True
        )
        # Space from the visible glyph, rather than the font's advance box.
        if is_left:
            return pin.bounds.left - PIN_NUMBER_GAP - bounds[2], y
        return pin.bounds.right + PIN_NUMBER_GAP - bounds[0], y

    def pin_number_bounds(self, pin: Pin, layout: PackageLayout) -> Rectangle:
        """Return exact visible number bounds, including multiple-digit numbers."""
        font = ImageFont.load_default(size=LABEL_FONT_SIZE)
        return Rectangle(*SvgDocument.text_bounds(
            self._number_position(pin, layout, font), str(pin.number), font=font,
            anchor="rm" if pin.number <= self.pin_count // 2 else "lm",
            bold=True,
        ))

    def render_package(
        self, draw: SvgDocument, layout: PackageLayout, ic_name: str
    ) -> None:
        """Draw beveled dark plastic, a top notch, pin-one dot, and centered name."""
        body = layout.body
        cx = (body.left + body.right) / 2
        cy = (body.top + body.bottom) / 2
        scale = self._detail_scale(layout)
        font = self._name_font(ic_name, body.right - body.left - 64 * scale, scale)

        draw.rounded_rectangle(
            body.box, radius=18 * scale, fill="#202226", outline="#151619",
            width=3 * scale,
        )
        draw.rounded_rectangle(
            (
                body.left + 12 * scale,
                body.top + 12 * scale,
                body.right - 12 * scale,
                body.bottom - 12 * scale,
            ),
            radius=12 * scale,
            fill="#33363B",
            outline="#4B4F55",
            width=2 * scale,
        )

        # A semicircular recess and molded dot establish the top-view orientation.
        notch_radius = 38 * scale
        draw.path(
            f"M {cx - notch_radius} {body.top} "
            f"A {notch_radius} {notch_radius} 0 0 0 "
            f"{cx + notch_radius} {body.top} Z",
            fill="#16181B",
            outline="#55595F",
            width=2 * scale,
        )
        marker_margin = 42 * scale
        marker_diameter = 57 * scale
        draw.ellipse(
            (
                body.left + marker_margin,
                body.top + marker_margin,
                body.left + marker_margin + marker_diameter,
                body.top + marker_margin + marker_diameter,
            ),
            fill="#202226",
            outline="#656A71",
            width=2 * scale,
        )
        draw.text((cx, cy), ic_name, font=font, fill="#F2F2F2", anchor="mm")
        draw.text(
            (cx, body.bottom - 48 * scale),
            f"DIP-{self.pin_count}",
            font=ImageFont.load_default(size=40 * scale),
            fill="#A6ABB0",
            anchor="mm",
        )

    @staticmethod
    def _name_font(
        name: str, available_width: float, scale: float
    ) -> ImageFont.FreeTypeFont:
        # Pillow's embedded font avoids system-dependent font substitution.
        for size in range(72, 17, -1):
            font = ImageFont.load_default(size=size * scale)
            if font.getlength(name) <= available_width:
                return font

        raise ValueError("IC name is too long to fit the DIP housing legibly.")
