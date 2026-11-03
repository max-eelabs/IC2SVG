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

"""Verify standard outlines, asymmetric numbering, assets, and input integration."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET

from components.input.loader import parse_input
from components.renderer import Orientation, PinDefinition, PinLabel, PinoutRenderer
from components.renderer.core.typography import PIN_NUMBER_GAP
from components.renderer.packages.registry import get_package
from components.renderer.packages.samples import generate_package_samples
from components.renderer.packages.sot23 import SUPPORTED_PIN_COUNTS, Sot23Renderer
from components.renderer.packages.sot23.catalog import load_variants


_DIRECTORY = Path(__file__).resolve().parents[1]
_SVG = "{http://www.w3.org/2000/svg}"


class Sot23Tests(unittest.TestCase):
    """Check geometry against manufacturer drawings rather than pixel snapshots."""

    def test_standard_dimensions_and_numbering(self) -> None:
        expected_positions = {
            3: ((-1, -0.95), (-1, 0.95), (1, 0)),
            5: ((-1, -0.95), (-1, 0), (-1, 0.95), (1, 0.95), (1, -0.95)),
            6: ((-1, -0.95), (-1, 0), (-1, 0.95),
                (1, 0.95), (1, 0), (1, -0.95)),
        }
        self.assertEqual(SUPPORTED_PIN_COUNTS, (3, 5, 6))
        for count, positions in expected_positions.items():
            renderer = Sot23Renderer(count)
            width, length, span, pitch = renderer.nominal_dimensions_mm
            self.assertEqual(length, 2.9)
            self.assertEqual(width, 1.3 if count == 3 else 1.6)
            self.assertEqual(span, 2.3 if count == 3 else 2.8)
            self.assertEqual(pitch, 1.9 if count == 3 else 0.95)
            for orientation in Orientation:
                with self.subTest(count=count, orientation=orientation):
                    layout = renderer.package_layout(orientation)
                    body = layout.body
                    units = (body.right - body.left) / width
                    self.assertAlmostEqual((body.bottom - body.top) / units, length)
                    cy = orientation.value[1] / 2
                    self.assertEqual([p.number for p in layout.pins],
                                     list(range(1, count + 1)))
                    for pin, (side, offset) in zip(layout.pins, positions):
                        bounds = pin.bounds
                        self.assertAlmostEqual(
                            ((bounds.top + bounds.bottom) / 2 - cy) / units, offset
                        )
                        if side == -1:
                            self.assertEqual(bounds.right, body.left)
                        else:
                            self.assertEqual(bounds.left, body.right)
                        self.assertGreater(bounds.left, 0)
                        self.assertLess(bounds.right, orientation.value[0])
                        self.assertGreater(bounds.top, body.top)
                        self.assertLess(bounds.bottom, body.bottom)
                        number = renderer.pin_number_bounds(pin, layout)
                        gap = (bounds.left - number.right if side == -1
                               else number.left - bounds.right)
                        self.assertAlmostEqual(gap, PIN_NUMBER_GAP)
                    actual_span = max(p.bounds.right for p in layout.pins) - min(
                        p.bounds.left for p in layout.pins
                    )
                    self.assertAlmostEqual(actual_span / units, span)

    def test_source_ranges_are_independent_of_geometry(self) -> None:
        for count in SUPPORTED_PIN_COUNTS:
            dimensions = Sot23Renderer(count).reference_dimensions
            expected = ("1.20-1.40", "2.80-3.00", "2.10-2.50", "1.90")
            if count != 3:
                expected = ("1.45-1.75", "2.75-3.05", "2.60-3.00", "0.95")
            self.assertEqual(tuple(row.millimeters for row in dimensions), expected)
            for row in dimensions:
                for inches, mm in zip(row.inches.split("-"),
                                      row.millimeters.split("-")):
                    self.assertAlmostEqual(float(inches), float(mm) / 25.4, places=4)

    def test_invalid_renderer_inputs(self) -> None:
        for count in (True, 3.0, "3", 0, 4, 7, 8):
            with self.subTest(count=count), self.assertRaises(ValueError):
                Sot23Renderer(count)
        renderer = Sot23Renderer()
        for name in ("", "two\nlines", "X" * 200):
            with self.subTest(name=name), self.assertRaises(ValueError):
                renderer.render(name)
        with self.assertRaises(TypeError):
            renderer.package_layout("landscape")

    def test_catalog_rejects_invalid_assets(self) -> None:
        data = json.loads((_DIRECTORY / "variants/sot23-5.json").read_text())
        mutations = (
            {"pin_count": 4},
            {"pin_count": 5.0},
            {"pin_positions": [[-1, -0.95]] * 5},
            {"pin_positions": data["pin_positions"][:-1]},
            {"pin_positions": [[-1, -0.95], [-1, -0.9], [-1, 0.95],
                               [1, 0.95], [1, -0.95]]},
            {"pin_positions": [[-1, float("nan")]] + data["pin_positions"][1:]},
            {"geometry_mm": {**data["geometry_mm"], "width": float("inf")}},
            {"geometry_mm": {**data["geometry_mm"], "span": 1.0}},
            {"geometry_mm": {**data["geometry_mm"], "length": 1.0}},
            {"reference": {}},
        )
        with TemporaryDirectory() as directory:
            path = Path(directory) / "variant.json"
            with self.assertRaisesRegex(ValueError, "No SOT-23 variant"):
                load_variants(directory)
            for mutation in mutations:
                with self.subTest(mutation=mutation):
                    path.write_text(json.dumps({**data, **mutation}))
                    with self.assertRaises(ValueError):
                        load_variants(directory)
            path.write_text(json.dumps(data))
            (Path(directory) / "duplicate.json").write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "duplicate SOT-23"):
                load_variants(directory)

    def test_discovery_samples_and_repeated_output(self) -> None:
        plugin = get_package("SOT-23")
        self.assertEqual(plugin.pin_counts, (3, 5, 6))
        with TemporaryDirectory() as directory:
            paths = generate_package_samples(plugin, directory)
            self.assertEqual(len(paths), 6)
            for path in paths:
                # Stored drawings can retain legacy XML encoding declarations.
                generated = ET.parse(path).getroot()
                stored = ET.parse(_DIRECTORY / "samples" / path.name).getroot()
                self.assertEqual(ET.tostring(generated), ET.tostring(stored))
            original = {path: path.read_bytes() for path in paths}
            generate_package_samples(plugin, directory)
            self.assertEqual(original, {path: path.read_bytes() for path in paths})

    def test_dense_portrait_requires_a_fitting_scale(self) -> None:
        renderer = PinoutRenderer(Sot23Renderer(6))
        labels = {
            number: (PinDefinition(1, PinLabel(f"SIG{number}")),
                     PinDefinition(2, PinLabel(f"ALT{number}")))
            for number in range(1, 7)
        }
        with self.assertRaisesRegex(ValueError, "cannot fit"):
            renderer.render("EXAMPLE", labels, Orientation.PORTRAIT,
                            content_scale=1.0)
        svg = renderer.render("EXAMPLE", labels, Orientation.PORTRAIT,
                              content_scale=0.4).to_string()
        root = ET.fromstring(svg)
        visible_labels = [group.get("aria-label") for group in
                          root.findall(f".//{_SVG}g[@aria-label]")]
        for number in range(1, 7):
            self.assertIn(f"SIG{number}", visible_labels)
            self.assertIn(f"ALT{number}", visible_labels)

    def test_json_input_annotations_and_colors(self) -> None:
        for count in SUPPORTED_PIN_COUNTS:
            for orientation in Orientation:
                data = {
                    "name": "EXAMPLE",
                    "package": {"family": "SOT-23", "pin_count": count},
                    "orientation": orientation.name.lower(),
                    "categories": {"io": {"name": "Signals", "color": "#123456"}},
                    "pins": [{"number": number, "type": "io", "definitions": [
                        {"column": 1, "category": "io", "name": f"SIG{number}"}
                    ]} for number in range(1, count + 1)],
                }
                original = deepcopy(data)
                request = parse_input(data)
                svg = request.render().to_string()
                self.assertEqual(request.render().to_string(), svg)
                self.assertEqual(data, original)
                root = ET.fromstring(svg)
                width, height = orientation.value
                self.assertEqual(root.get("viewBox"), f"0 0 {width} {height}")
                labels = [group.get("aria-label") for group in
                          root.findall(f".//{_SVG}g[@aria-label]")]
                self.assertEqual(labels[:count], [str(n) for n in range(1, count + 1)])
                self.assertEqual(labels.count("I/O"), count)
                for number in range(1, count + 1):
                    self.assertIn(f"SIG{number}", labels)
                self.assertIn("#123456", svg)
                self.assertFalse(root.findall(f".//{_SVG}image"))
                self.assertFalse(root.findall(f".//{_SVG}text"))


if __name__ == "__main__":
    unittest.main()
