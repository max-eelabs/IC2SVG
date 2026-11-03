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

"""Replaceable strategies for drawing pin connector lines."""

from abc import ABC, abstractmethod

from ..core import SvgDocument


class LineRenderer(ABC):
    """Draw a connector between its visible start and end positions.

    Implementations must keep their longitudinal extent between start and end;
    caps and decorations must not extend into the surrounding gaps. Thickness
    describes the full vertical extent so the compositor can check canvas bounds.
    All dimensions are SVG logical units.
    """

    preferred_length: float = 120.0
    minimum_length: float = 24.0
    thickness: float = 2.0

    @abstractmethod
    def render(
        self, document: SvgDocument, start: float, end: float, y: float
    ) -> None:
        """Draw into the document; start may be rightward or leftward of end."""


class StraightLineRenderer(LineRenderer):
    """Draw a dark gray horizontal line with flat ends."""

    def render(
        self, document: SvgDocument, start: float, end: float, y: float
    ) -> None:
        """Draw a flat-ended SVG stroke within the supplied endpoints."""
        document.line((start, y, end, y), fill="#4B4F55", width=self.thickness)
