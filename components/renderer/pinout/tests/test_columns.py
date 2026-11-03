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

"""Check outward column reservation, alignment, and visible annotation gaps."""

import unittest

from components.renderer import (
    DipRenderer, Orientation, PinDefinition, PinLabel, PinoutRenderer, Rectangle,
    RoundedDefinitionRenderer, SvgDocument,
)


class _RecordingDefinitions(RoundedDefinitionRenderer):
    """Record visible allocations while retaining the real drawing strategy."""

    def __init__(self) -> None:
        self.boxes: dict[str, Rectangle] = {}

    def render(
        self, document: SvgDocument, label: PinLabel, bounds: Rectangle
    ) -> None:
        self.boxes[label.text] = bounds
        super().render(document, label, bounds)


class ColumnTests(unittest.TestCase):
    """Keep explicit slots stable across pins, empty columns, and orientations."""

    def test_columns_do_not_collapse_when_empty(self) -> None:
        for orientation in Orientation:
            definitions = _RecordingDefinitions()
            renderer = PinoutRenderer(
                DipRenderer(8), definition_renderer=definitions
            )
            # Same-size labels allow comparing columns without text-width noise.
            renderer.render("TEST", {
                1: [PinDefinition(1, PinLabel("A")),
                    PinDefinition(2, PinLabel("B"))],
                2: [PinDefinition(2, PinLabel("C"))],
                8: [PinDefinition(1, PinLabel("D")),
                    PinDefinition(2, PinLabel("E"))],
                7: [PinDefinition(2, PinLabel("F"))],
            }, orientation)
            self.assertAlmostEqual(definitions.boxes["B"].right,
                                   definitions.boxes["C"].right, places=5)
            self.assertAlmostEqual(definitions.boxes["E"].left,
                                   definitions.boxes["F"].left, places=5)
            self.assertLess(definitions.boxes["B"].right, definitions.boxes["A"].left)
            self.assertGreater(
                definitions.boxes["E"].left, definitions.boxes["D"].right
            )

    def test_globally_empty_column_and_duplicate_columns(self) -> None:
        definitions = _RecordingDefinitions()
        chip = DipRenderer(8)
        renderer = PinoutRenderer(chip, definition_renderer=definitions)
        renderer.render("TEST", {1: [PinDefinition(2, PinLabel("A"))]})
        sparse = definitions.boxes["A"].right
        renderer.render("TEST", {1: [PinDefinition(1, PinLabel("A"))]})
        self.assertLess(sparse, definitions.boxes["A"].right)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            renderer.render("TEST", {1: [PinDefinition(1, PinLabel("A")),
                                        PinDefinition(1, PinLabel("B"))]})

    def test_column_widths_and_visible_gaps_are_uniform(self) -> None:
        labels = {
            1: [PinDefinition(1, PinLabel("PB5")),
                PinDefinition(2, PinLabel("A"))],
            2: [PinDefinition(1, PinLabel("GND")),
                PinDefinition(2, PinLabel("LONG LABEL"))],
            8: [PinDefinition(1, PinLabel("VCC")),
                PinDefinition(2, PinLabel("B"))],
            7: [PinDefinition(2, PinLabel("C"))],
        }
        standard = RoundedDefinitionRenderer()
        expected_widths = {
            1: max(standard.measure(item.label).width
                   for row in labels.values() for item in row if item.column == 1),
            2: standard.measure(PinLabel("LONG LABEL")).width,
        }
        for orientation in Orientation:
            definitions = _RecordingDefinitions()
            chip = DipRenderer(8)
            PinoutRenderer(chip, definition_renderer=definitions).render(
                "TEST", labels, orientation, content_scale=0.5
            )
            layout = chip.package_layout(orientation)
            gaps = []
            for number, row in labels.items():
                pin = layout.pins[number - 1]
                number_box = chip.pin_number_bounds(pin, layout)
                for item in row:
                    box = definitions.boxes[item.label.text]
                    self.assertAlmostEqual(
                        box.right - box.left, expected_widths[item.column]
                    )
                if len(row) == 2:
                    inner = definitions.boxes[row[0].label.text]
                    outer = definitions.boxes[row[1].label.text]
                    if number <= 4:
                        gap = inner.left - outer.right
                        pin_gap = pin.bounds.left - number_box.right
                    else:
                        gap = outer.left - inner.right
                        pin_gap = number_box.left - pin.bounds.right
                    self.assertAlmostEqual(gap, pin_gap)
                    gaps.append(gap)
            self.assertAlmostEqual(min(gaps), max(gaps))


if __name__ == "__main__":
    unittest.main()
