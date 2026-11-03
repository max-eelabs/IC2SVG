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

"""Electrical pin roles and their shared neutral badge style."""

from enum import Enum

from PIL import ImageFont

from ..core import Rectangle, SvgDocument
from ..core.typography import DEFINITION_SCALE, LABEL_FONT_SIZE
from ..definition import (
    DefinitionRenderer, DefinitionSize, PinLabel, RoundedDefinitionRenderer,
)


PIN_TYPE_BACKGROUND = "#EEEEEE"

PIN_TYPE_TEXT_COLOR = "#555555"


class PinType(str, Enum):
    """Electrical role of a physical pin, separate from alternate functions."""

    INPUT = "input"
    OUTPUT = "output"
    IO = "io"
    POWER = "power"
    NC = "nc"

    @property
    def label(self) -> PinLabel:
        """Return a neutral badge with the fixed display name for this role."""
        return PinLabel(
            _DISPLAY_NAMES[self], PIN_TYPE_BACKGROUND, PIN_TYPE_TEXT_COLOR
        )


_DISPLAY_NAMES = {
    PinType.INPUT: "IN",
    PinType.OUTPUT: "OUT",
    PinType.IO: "I/O",
    PinType.POWER: "PWR",
    PinType.NC: "NC",
}


class _PinTypeRenderer(DefinitionRenderer):
    """Keep neutral badges within a row's available height on long packages."""

    def __init__(self, maximum_height: float) -> None:
        self._scale = min(1.0, maximum_height / (49 * DEFINITION_SCALE))
        self._standard = RoundedDefinitionRenderer()

    def measure(self, label: PinLabel) -> DefinitionSize:
        """Measure the badge at a uniform scale constrained by physical row pitch."""
        size = self._standard.measure(label)
        return DefinitionSize(size.width * self._scale, size.height * self._scale)

    def render(
        self, document: SvgDocument, label: PinLabel, bounds: Rectangle
    ) -> None:
        """Draw a neutral rounded badge with proportionally scaled font outlines."""
        scale = DEFINITION_SCALE * self._scale
        inset = scale / 2
        document.rounded_rectangle(
            (bounds.left + inset, bounds.top + inset,
             bounds.right - inset, bounds.bottom - inset),
            radius=5 * scale, fill=PIN_TYPE_BACKGROUND,
            outline="#4B4F55", width=scale,
        )
        document.text(
            ((bounds.left + bounds.right) / 2, (bounds.top + bounds.bottom) / 2),
            label.text, font=ImageFont.load_default(size=LABEL_FONT_SIZE * self._scale),
            fill=PIN_TYPE_TEXT_COLOR, anchor="mm", bold=True,
        )
