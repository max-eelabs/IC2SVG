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

"""Draw outward connector lines and optional colored pin labels."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite

from ..core import IcRenderer, Orientation, Rectangle, SvgDocument
from ..definition import (
    DefinitionRenderer, DefinitionSize, PinDefinition, PinLabel,
    RoundedDefinitionRenderer,
)
from ..line import LineRenderer, StraightLineRenderer
from .types import PinType, _PinTypeRenderer


@dataclass(frozen=True)
class _MeasuredDefinition:
    """A definition and the visible bounds requested by its drawing strategy."""

    column: int
    label: PinLabel
    size: DefinitionSize
    renderer: DefinitionRenderer


@dataclass(frozen=True)
class _Connector:
    """Measured annotation data consumed by the compositor."""

    number: int
    start: float
    y: float
    direction: int
    gap: float
    definitions: tuple[_MeasuredDefinition, ...]
    reserved_width: float


class PinoutRenderer:
    """Compose reusable pin annotations around an existing package renderer.

    Owns placement and spacing; delegates all annotation drawing and definition
    measurement to injected strategies. Pin-to-number, number-to-line, and
    line-to-definition gaps match. All dimensions are SVG logical units.
    """

    def __init__(
        self,
        chip_renderer: IcRenderer,
        *,
        line_renderer: LineRenderer | None = None,
        definition_renderer: DefinitionRenderer | None = None,
    ) -> None:
        """Compose independent package, line, and definition renderers.

        Omitted strategies use straight gray lines and rounded colored boxes.
        Custom strategies implement the corresponding abstract renderer contracts.
        """
        self._chip_renderer = chip_renderer
        self._line_renderer = (
            StraightLineRenderer() if line_renderer is None else line_renderer
        )
        self._definition_renderer = (
            RoundedDefinitionRenderer()
            if definition_renderer is None else definition_renderer
        )

    def render(
        self,
        ic_name: str,
        labels: Mapping[int, PinLabel | Sequence[PinDefinition]] | None = None,
        orientation: Orientation = Orientation.LANDSCAPE,
        *,
        content_scale: float = 0.6,
        pin_types: Mapping[int, PinType] | None = None,
    ) -> SvgDocument:
        """Draw the chip, connector lines, and explicitly positioned definitions.

        A single PinLabel is shorthand for one definition in column one. Explicit
        columns count outward; empty columns reserve their measured slot width.
        When supplied, pin_types must classify every physical pin. Neutral type
        badges occupy a separate first slot nearest the chip; function columns
        retain their original numbering and shift outward by one display slot.
        Caller-owned mappings and sequences are not mutated.

        Raises:
            ValueError: A label references an absent pin or cannot fit the canvas.
            TypeError: A label key or value has an unsupported type.
        """
        document = self._chip_renderer.render(
            ic_name, orientation, content_scale=content_scale
        )
        layout = self._chip_renderer.package_layout(orientation)
        labels = {} if labels is None else dict(labels)
        pin_numbers = {pin.number for pin in layout.pins}
        measured: dict[int, tuple[_MeasuredDefinition, ...]] = {}
        column_widths: dict[int, float] = {}
        if pin_types is not None:
            pin_types = dict(pin_types)
            if any(type(number) is not int for number in pin_types):
                raise TypeError("Pin type keys must be integer physical pin numbers.")
            if set(pin_types) != pin_numbers:
                raise ValueError("Pin types must classify every physical pin exactly.")
            if any(not isinstance(role, PinType) for role in pin_types.values()):
                raise TypeError("Pin types must use PinType values.")
            row_centers = sorted({
                (pin.bounds.top + pin.bounds.bottom) / 2 for pin in layout.pins
            })
            row_pitch = min(
                (lower - upper for upper, lower in zip(row_centers, row_centers[1:])),
                default=float("inf"),
            )
            type_renderer = _PinTypeRenderer(maximum_height=row_pitch * 0.8)
            for pin in layout.pins:
                label = pin_types[pin.number].label
                size = type_renderer.measure(label)
                column_widths[1] = max(column_widths.get(1, 0), size.width)
                measured[pin.number] = (
                    _MeasuredDefinition(1, label, size, type_renderer),
                )

        for number, value in labels.items():
            if type(number) is not int:
                raise TypeError("Pin numbers must be integers.")
            if number not in pin_numbers:
                raise ValueError(f"No physical pin {number} exists on this package.")
            if isinstance(value, PinLabel):
                definitions = (PinDefinition(1, value),)
            elif isinstance(value, Sequence):
                definitions = tuple(value)
            else:
                definitions = None
            if definitions is None or any(
                not isinstance(item, PinDefinition) for item in definitions
            ):
                raise TypeError("Use PinLabel or a sequence of PinDefinition per pin.")
            if len({item.column for item in definitions}) != len(definitions):
                raise ValueError(f"Pin {number} has duplicate definition columns.")
            items = list(measured.get(number, ()))
            for definition in sorted(definitions, key=lambda item: item.column):
                size = self._definition_renderer.measure(definition.label)
                column = definition.column + (pin_types is not None)
                column_widths[column] = max(column_widths.get(column, 0), size.width)
                items.append(_MeasuredDefinition(
                    column, definition.label, size, self._definition_renderer
                ))
            measured[number] = tuple(items)

        # Even a column unused by every pin must reserve a real outward slot.
        fallback_width = max(column_widths.values(), default=0)
        max_column = max(column_widths, default=0)
        slot_widths = tuple(
            column_widths.get(column, fallback_width)
            for column in range(1, max_column + 1)
        )
        # Place annotations within the actual visible sheet after content scaling.
        sheet_scale = document.content_scale
        extra_x = document.size[0] * (1 / sheet_scale - 1) / 2
        extra_y = document.size[1] * (1 / sheet_scale - 1) / 2
        canvas = Rectangle(
            -extra_x, -extra_y, document.size[0] + extra_x,
            document.size[1] + extra_y,
        )

        line_renderer = self._line_renderer
        if (
            any(not isfinite(value) or value <= 0 for value in (
                line_renderer.minimum_length, line_renderer.preferred_length,
                line_renderer.thickness,
            ))
            or line_renderer.minimum_length > line_renderer.preferred_length
        ):
            raise ValueError(
                "Line renderer dimensions must be positive and consistent."
            )
        connectors: list[_Connector] = []
        line_length = line_renderer.preferred_length
        for pin in layout.pins:
            number = self._chip_renderer.pin_number_bounds(pin, layout)
            is_left = pin.bounds.right <= layout.body.left
            direction = -1 if is_left else 1
            gap = (
                pin.bounds.left - number.right if is_left
                else number.left - pin.bounds.right
            )
            start = number.left - gap if is_left else number.right + gap
            y = (pin.bounds.top + pin.bounds.bottom) / 2
            definitions = measured.get(pin.number, ())
            reserved_width = max((
                sum(slot_widths[:item.column - 1])
                + gap * item.column + slot_widths[item.column - 1]
                for item in definitions
            ), default=0)
            connectors.append(
                _Connector(pin.number, start, y, direction, gap, definitions,
                           reserved_width)
            )

        # Align column origins across rows. Slightly different number widths are
        # absorbed by line lengths, preserving all visible number and box gaps.
        common_starts = {}
        for direction in {connector.direction for connector in connectors}:
            starts = [c.start for c in connectors if c.direction == direction]
            common_starts[direction] = min(starts) if direction == -1 else max(starts)
        for connector in connectors:
            start = (
                common_starts[connector.direction] if max_column > 1
                else connector.start
            )
            available = (
                start - canvas.left if connector.direction == -1
                else canvas.right - start
            )
            line_length = min(line_length, available - connector.reserved_width - 4)

        if line_length < line_renderer.minimum_length:
            raise ValueError("Pin annotations cannot fit the selected canvas.")

        # Single-column output retains its established equal line lengths.
        definition_boxes: list[Rectangle] = []
        for connector in connectors:
            start_edge = (
                common_starts[connector.direction] if max_column > 1
                else connector.start
            )
            end = start_edge + connector.direction * line_length
            half_thickness = line_renderer.thickness / 2
            if not canvas.top + half_thickness <= connector.y <= (
                canvas.bottom - half_thickness
            ):
                raise ValueError("Pin connector thickness exceeds the canvas bounds.")
            line_renderer.render(document, connector.start, end, connector.y)

            for item in connector.definitions:
                column = item.column
                offset = sum(slot_widths[:column - 1]) + connector.gap * column
                near_edge = end + connector.direction * offset
                size = item.size
                width = slot_widths[column - 1]
                left = (
                    near_edge - width if connector.direction == -1 else near_edge
                )
                box = Rectangle(
                    left, connector.y - size.height / 2,
                    left + width, connector.y + size.height / 2,
                )
                if (
                    box.left < canvas.left or box.right > canvas.right
                    or box.top < canvas.top or box.bottom > canvas.bottom
                ):
                    raise ValueError(
                        f"Definition on pin {connector.number} cannot fit the canvas."
                    )
                if any(
                    box.left < other.right and box.right > other.left
                    and box.top < other.bottom and box.bottom > other.top
                    for other in definition_boxes
                ):
                    raise ValueError(
                        f"Definition on pin {connector.number} overlaps another pin."
                    )
                definition_boxes.append(box)
                item.renderer.render(document, item.label, box)

        return document
