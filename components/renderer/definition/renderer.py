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

"""Replaceable strategies for measuring and drawing pin definitions."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isfinite

from PIL import ImageFont

from ..core import Rectangle, SvgDocument
from ..core.typography import DEFINITION_SCALE, LABEL_FONT_SIZE
from .model import PinLabel
from .text import parse_signal_text


@dataclass(frozen=True)
class DefinitionSize:
    """Full visible definition extents, including any border or decoration."""

    width: float
    height: float

    def __post_init__(self) -> None:
        """Reject extents that cannot participate in layout."""
        if any(not isfinite(value) or value <= 0
               for value in (self.width, self.height)):
            raise ValueError("Definition width and height must be finite and positive.")


class DefinitionRenderer(ABC):
    """Measure and draw a definition using full visible bounds in logical units.

    Measurement must be deterministic. Rendering must remain within the bounds
    allocated from that measurement, including strokes, shadows, and lettering.
    """

    @abstractmethod
    def measure(self, label: PinLabel) -> DefinitionSize:
        """Return the visible dimensions required for this label."""

    @abstractmethod
    def render(
        self, document: SvgDocument, label: PinLabel, bounds: Rectangle
    ) -> None:
        """Draw the definition inside its measured bounds on the caller's canvas."""


class RoundedDefinitionRenderer(DefinitionRenderer):
    """Draw colored boxes and vector lettering with optional uniform scaling."""

    # Preserve subclasses whose existing constructors do not call super().
    _scale = 1.0

    def __init__(self, *, scale: float = 1.0) -> None:
        """Select a positive uniform scale for measurement, text, and decoration."""
        if not isfinite(scale) or scale <= 0:
            raise ValueError("Definition scale must be finite and positive.")
        self._scale = scale

    def measure(self, label: PinLabel) -> DefinitionSize:
        """Reserve the uniformly enlarged visible dimensions, including borders."""
        font = ImageFont.load_default(size=28)
        signal = parse_signal_text(label.text)
        scale = DEFINITION_SCALE * self._scale
        return DefinitionSize((font.getlength(signal.text) + 33) * scale, 49 * scale)

    def render(
        self, document: SvgDocument, label: PinLabel, bounds: Rectangle
    ) -> None:
        """Inset the border's centerline so painted edges match allocated bounds."""
        signal = parse_signal_text(label.text)
        scale = DEFINITION_SCALE * self._scale
        font = ImageFont.load_default(size=LABEL_FONT_SIZE * self._scale)
        center = ((bounds.left + bounds.right) / 2,
                  (bounds.top + bounds.bottom) / 2)
        inset = scale / 2
        document.rounded_rectangle(
            (bounds.left + inset, bounds.top + inset,
             bounds.right - inset, bounds.bottom - inset),
            radius=5 * scale, fill=label.color,
            outline="#4B4F55", width=scale,
        )
        document.text(
            center, signal.text, font=font,
            fill=label.text_color, anchor="mm", bold=True,
        )
        origin = center[0] - font.getlength(signal.text) / 2
        for start, end in signal.overbars:
            # Match the actual glyph positions, including kerning at the boundary.
            offset = (
                font.getlength(signal.text[:start + 1])
                - font.getlength(signal.text[start])
            )
            left, top, right, _ = document.text_bounds(
                (origin + offset, center[1]), signal.text[start:end],
                font=font, anchor="lm", bold=True,
            )
            y = top - font.size * 0.12
            document.line(
                (left, y, right, y), fill=label.text_color, width=font.size * 0.065
            )
