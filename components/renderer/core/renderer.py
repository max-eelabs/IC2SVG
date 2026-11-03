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

"""Shared rendering contract and geometry in SVG logical units, viewed from above."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .svg import SvgDocument


class Orientation(Enum):
    """Supported canvas orientations, with exact output dimensions."""

    LANDSCAPE = (1920, 1080)
    PORTRAIT = (1080, 1920)


@dataclass(frozen=True)
class Rectangle:
    """Logical bounds; x increases rightward and y increases downward."""

    left: float
    top: float
    right: float
    bottom: float

    @property
    def box(self) -> tuple[float, float, float, float]:
        """Return bounds as left, top, right, bottom."""
        return self.left, self.top, self.right, self.bottom


@dataclass(frozen=True)
class Pin:
    """Physical pin number and its visible metal footprint."""

    number: int
    bounds: Rectangle


@dataclass(frozen=True)
class PackageLayout:
    """Immutable body and pins, with pins ordered by physical number."""

    body: Rectangle
    pins: tuple[Pin, ...]


@dataclass(frozen=True)
class PackageDimension:
    """One published measurement, with explicit inch and millimeter text.

    Values may include ranges and source qualifiers. They are displayed verbatim
    without unit conversion, preserving the package specification's precision.
    """

    label: str
    inches: str
    millimeters: str

    def __post_init__(self) -> None:
        """Reject empty or multiline reference text before rendering."""
        for value in (self.label, self.inches, self.millimeters):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Package dimension fields must be nonempty strings.")
            if any(character in value for character in "\r\n\t"):
                raise ValueError("Package dimension fields must occupy one line.")


class IcRenderer(ABC):
    """Define package geometry and rules for drawing the housing and pins.

    Subclasses provide a top-view layout and draw into the supplied canvas.
    Rendering creates a fresh vector document and does not write files or retain
    state. Geometry, lettering, and strokes scale together through the SVG viewBox.
    """

    @property
    @abstractmethod
    def pin_count(self) -> int:
        """Return the total physical pin count for this package variant."""

    @property
    @abstractmethod
    def reference_dimensions(self) -> tuple[PackageDimension, ...]:
        """Return ordered, fixed reference measurements for the selected variant."""

    def render(
        self,
        ic_name: str,
        orientation: Orientation = Orientation.LANDSCAPE,
        *,
        content_scale: float = 0.6,
    ) -> SvgDocument:
        """Draw a named IC at 60% scale on a sheet of the selected exact size.

        Content scale changes the drawing's footprint without changing the sheet
        or logical layout coordinates. Use 1.0 for the original sheet occupancy.

        Raises:
            ValueError: The name is empty, multiline, or cannot fit the housing.
            TypeError: The name or orientation has an unsupported type.
        """
        if not isinstance(ic_name, str):
            raise TypeError("IC name must be a string.")
        if not isinstance(orientation, Orientation):
            raise TypeError("Orientation must be an Orientation enum member.")
        if not ic_name.strip() or any(char in ic_name for char in "\r\n\t"):
            raise ValueError("IC name must be nonempty and occupy one line.")

        layout = self.package_layout(orientation)
        document = SvgDocument(orientation.value, content_scale=content_scale)
        self.render_pins(document, layout)
        self.render_package(document, layout, ic_name.strip())
        return document

    @abstractmethod
    def package_layout(self, orientation: Orientation) -> PackageLayout:
        """Return package bounds and numbered pins for the selected canvas."""

    @abstractmethod
    def pin_number_bounds(self, pin: Pin, layout: PackageLayout) -> Rectangle:
        """Return visible pin-number bounds for placing outward annotations."""

    @abstractmethod
    def render_pins(self, draw: SvgDocument, layout: PackageLayout) -> None:
        """Draw metal pins and their physical numbers onto the caller's canvas."""

    @abstractmethod
    def render_package(
        self, draw: SvgDocument, layout: PackageLayout, ic_name: str
    ) -> None:
        """Draw the housing, orientation marker, and IC name.

        Raises:
            ValueError: The IC name cannot fit legibly inside the housing.
        """
