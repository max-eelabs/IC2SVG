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

"""Behavior checks for annotation placement around package drawings."""

import unittest
from xml.etree import ElementTree as ET

from components.renderer import (
    DefinitionRenderer, DefinitionSize, DipRenderer, LineRenderer, Orientation,
    PinLabel, PinoutRenderer, Rectangle, SvgDocument,
)


_SVG = "{http://www.w3.org/2000/svg}"


class _AlternateLineRenderer(LineRenderer):
    """Test an independently implemented connector strategy."""

    preferred_length = 60.0
    minimum_length = 20.0
    thickness = 3.0

    def render(
        self, document: SvgDocument, start: float, end: float, y: float
    ) -> None:
        document.line((start, y, end, y), fill="#112233", width=self.thickness)


class _AlternateDefinitionRenderer(DefinitionRenderer):
    """Test nonrectangular definitions with independent measurement."""

    def __init__(self) -> None:
        self.boxes: list[Rectangle] = []

    def measure(self, label: PinLabel) -> DefinitionSize:
        return DefinitionSize(100 if label.text == "GND" else 80, 60)

    def render(
        self, document: SvgDocument, label: PinLabel, bounds: Rectangle
    ) -> None:
        self.boxes.append(bounds)
        document.ellipse(
            (bounds.left + 0.5, bounds.top + 0.5,
             bounds.right - 0.5, bounds.bottom - 0.5),
            fill=label.color, outline="#112233", width=1,
        )


class PinoutTests(unittest.TestCase):
    """Check connector gaps, power labels, and annotation validation."""

    def test_equal_visible_gaps_and_line_lengths(self) -> None:
        for count in (8, 16, 28):
            for orientation in Orientation:
                with self.subTest(count=count, orientation=orientation):
                    chip = DipRenderer(count)
                    layout = chip.package_layout(orientation)
                    root = ET.fromstring(
                        PinoutRenderer(chip).render("TEST", orientation=orientation)
                        .to_string()
                    )
                    lines = [
                        line for line in root.findall(f".//{_SVG}line")
                        if line.get("stroke") == "#4B4F55"
                    ]
                    self.assertEqual(len(lines), count)
                    lengths = []
                    for pin, line in zip(layout.pins, lines):
                        bounds = chip.pin_number_bounds(pin, layout)
                        start, end = float(line.get("x1")), float(line.get("x2"))
                        is_left = pin.number <= count // 2
                        if is_left:
                            pin_gap = pin.bounds.left - bounds.right
                            line_gap = bounds.left - start
                            self.assertLess(end, start)
                        else:
                            pin_gap = bounds.left - pin.bounds.right
                            line_gap = start - bounds.right
                            self.assertGreater(end, start)
                        self.assertAlmostEqual(pin_gap, line_gap, places=5)
                        self.assertEqual(line.get("y1"), line.get("y2"))
                        self.assertGreaterEqual(min(start, end), 0)
                        self.assertLessEqual(max(start, end), orientation.value[0])
                        lengths.append(abs(end - start))
                    self.assertAlmostEqual(min(lengths), max(lengths), places=5)

    def test_power_labels_and_determinism(self) -> None:
        renderer = PinoutRenderer(DipRenderer(8))
        labels = {
            4: PinLabel("GND", "#202020", "#FFFFFF"),
            8: PinLabel("VCC", "#E53935", "#FFFFFF"),
        }
        for orientation in Orientation:
            svg = renderer.render("TEST-IC", labels, orientation).to_string()
            self.assertEqual(
                svg, renderer.render("TEST-IC", labels, orientation).to_string()
            )
            root = ET.fromstring(svg)
            names = [
                g.get("aria-label") for g in root.findall(f".//{_SVG}g[@aria-label]")
            ]
            self.assertEqual(names[-2:], ["GND", "VCC"])
            boxes = [
                box for box in root.findall(f".//{_SVG}rect")
                if box.get("fill") in ("#202020", "#E53935")
            ]
            self.assertEqual(len(boxes), 2)
            lines = [
                line for line in root.findall(f".//{_SVG}line")
                if line.get("stroke") == "#4B4F55"
            ]
            for box, index in zip(boxes, (3, 7)):
                self.assertAlmostEqual(
                    float(box.get("y")) + float(box.get("height")) / 2,
                    float(lines[index].get("y1")),
                )
                chip = DipRenderer(8)
                layout = chip.package_layout(orientation)
                pin = layout.pins[index]
                number = chip.pin_number_bounds(pin, layout)
                border = float(box.get("stroke-width")) / 2
                end = float(lines[index].get("x2"))
                if index == 3:
                    visible_edge = (
                        float(box.get("x")) + float(box.get("width")) + border
                    )
                    pin_gap = pin.bounds.left - number.right
                    definition_gap = end - visible_edge
                else:
                    visible_edge = float(box.get("x")) - border
                    pin_gap = number.left - pin.bounds.right
                    definition_gap = visible_edge - end
                self.assertAlmostEqual(definition_gap, pin_gap, places=5)
            self.assertFalse(root.findall(f".//{_SVG}image"))

    def test_strategies_are_abstract_and_replaceable(self) -> None:
        with self.assertRaises(TypeError):
            LineRenderer()
        with self.assertRaises(TypeError):
            DefinitionRenderer()

        for orientation in Orientation:
            definitions = _AlternateDefinitionRenderer()
            chip = DipRenderer(8)
            renderer = PinoutRenderer(
                chip, line_renderer=_AlternateLineRenderer(),
                definition_renderer=definitions,
            )
            root = ET.fromstring(renderer.render(
                "TEST", {4: PinLabel("GND"), 8: PinLabel("VCC")}, orientation
            ).to_string())
            lines = [
                line for line in root.findall(f".//{_SVG}line")
                if line.get("stroke") == "#112233"
            ]
            self.assertEqual(len(lines), 8)
            self.assertEqual(len(definitions.boxes), 2)
            layout = chip.package_layout(orientation)
            for box, index, width in zip(definitions.boxes, (3, 7), (100, 100)):
                self.assertAlmostEqual(box.right - box.left, width)
                self.assertEqual(box.bottom - box.top, 60)
                pin = layout.pins[index]
                number = chip.pin_number_bounds(pin, layout)
                end = float(lines[index].get("x2"))
                if index == 3:
                    self.assertAlmostEqual(end - box.right,
                                           pin.bounds.left - number.right, places=5)
                else:
                    self.assertAlmostEqual(box.left - end,
                                           number.left - pin.bounds.right, places=5)
            self.assertEqual(len(root.findall(f".//{_SVG}ellipse")), 3)

    def test_invalid_definition_dimensions(self) -> None:
        for width, height in ((0, 40), (80, -1), (float("nan"), 20)):
            with self.assertRaises(ValueError):
                DefinitionSize(width, height)

    def test_content_scale_keeps_sheet_size_and_all_relative_spacing(self) -> None:
        class ShortLines(_AlternateLineRenderer):
            """Keep this fixture within the full-size portrait viewport too."""

            preferred_length = 24.0
            minimum_length = 24.0

        renderer = PinoutRenderer(DipRenderer(8), line_renderer=ShortLines())
        labels = {4: PinLabel("A"), 8: PinLabel("B")}
        for orientation in Orientation:
            small = renderer.render("TEST-IC", labels, orientation)
            full = renderer.render("TEST-IC", labels, orientation, content_scale=1)
            self.assertEqual(small.size, full.size)
            root = ET.fromstring(small.to_string())
            original = ET.fromstring(full.to_string())
            drawing = root.find(f"{_SVG}g[@id='drawing']")
            width, height = orientation.value
            self.assertEqual(
                drawing.get("transform"),
                f"translate({width * 0.2:g} {height * 0.2:g}) scale(0.6)",
            )
            self.assertEqual(
                [ET.tostring(child) for child in drawing],
                [ET.tostring(child) for child in original][1:],
            )
            self.assertEqual(root[0].get("width"), str(width))
            self.assertEqual(root[0].get("height"), str(height))
        for scale in (0, -1, 1.1, float("inf"), float("nan")):
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                renderer.render("TEST", content_scale=scale)

    def test_pin_numbers_match_definition_font_and_larger_equal_gaps(self) -> None:
        for count in (8, 28):
            for orientation in Orientation:
                chip = DipRenderer(count)
                root = ET.fromstring(PinoutRenderer(chip).render(
                    "TEST", {count: PinLabel("VCC")}, orientation
                ).to_string())
                number = root.find(f".//{_SVG}g[@aria-label='{count}']")
                label = root.find(f".//{_SVG}g[@aria-label='VCC']")
                number_scale = number.find(f"{_SVG}path").get("transform")
                label_scale = label.find(f"{_SVG}path").get("transform")
                self.assertEqual(number_scale.split("scale(")[1],
                                 label_scale.split("scale(")[1])
                self.assertEqual(number.get("stroke-width"), label.get("stroke-width"))
                layout = chip.package_layout(orientation)
                pin = layout.pins[-1]
                bounds = chip.pin_number_bounds(pin, layout)
                self.assertAlmostEqual(bounds.left - pin.bounds.right, 28)
                lines = [
                    line for line in root.findall(f".//{_SVG}line")
                    if line.get("stroke") == "#4B4F55"
                ]
                self.assertAlmostEqual(
                    float(lines[-1].get("x1")) - bounds.right, 28, places=5
                )

    def test_invalid_labels_and_overflow(self) -> None:
        renderer = PinoutRenderer(DipRenderer(8))
        with self.assertRaises(ValueError):
            renderer.render("TEST", {9: PinLabel("VCC")})
        with self.assertRaises(TypeError):
            renderer.render("TEST", {True: PinLabel("VCC")})
        with self.assertRaises(TypeError):
            renderer.render("TEST", {8: "VCC"})
        for text in ("", "   ", "two\nlines"):
            with self.assertRaises(ValueError):
                PinLabel(text)
        with self.assertRaises(ValueError):
            PinLabel("VCC", "invalid-color")
        with self.assertRaises(ValueError):
            renderer.render("TEST", {8: PinLabel("X" * 100)})


if __name__ == "__main__":
    unittest.main()
