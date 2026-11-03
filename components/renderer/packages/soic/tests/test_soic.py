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

"""Verify SOIC outlines, counterclockwise numbering, and package integration."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET

from components.input.loader import parse_input
from components.renderer import Orientation, PinLabel
from components.renderer.core.typography import PIN_NUMBER_GAP
from components.renderer.packages.registry import get_package
from components.renderer.packages.samples import generate_package_samples
from components.renderer.packages.soic import SUPPORTED_PIN_COUNTS, SoicRenderer
from components.renderer.packages.soic.catalog import load_variants


_DIRECTORY = Path(__file__).resolve().parents[1]
_SVG = "{http://www.w3.org/2000/svg}"


class SoicTests(unittest.TestCase):
    """Check public contracts against the selected narrow-body TI drawings."""

    def test_standard_geometry_numbering_and_visible_bounds(self) -> None:
        self.assertEqual(SUPPORTED_PIN_COUNTS, (8, 14, 16))
        for count, length in ((8, 4.9), (14, 8.65), (16, 9.9)):
            renderer = SoicRenderer(count)
            self.assertEqual(renderer.nominal_dimensions_mm, (3.9, length, 6.0, 1.27))
            for orientation in Orientation:
                with self.subTest(count=count, orientation=orientation):
                    layout = renderer.package_layout(orientation)
                    body = layout.body
                    units = (body.right - body.left) / 3.9
                    self.assertAlmostEqual((body.bottom - body.top) / units, length)
                    pins = layout.pins
                    rows = count // 2
                    self.assertEqual([pin.number for pin in pins],
                                     list(range(1, count + 1)))
                    self.assertEqual(pins[0].bounds.top, pins[-1].bounds.top)
                    self.assertEqual(pins[rows - 1].bounds.top, pins[rows].bounds.top)
                    for index, pin in enumerate(pins):
                        bounds = pin.bounds
                        is_left = index < rows
                        if is_left:
                            self.assertEqual(bounds.right, body.left)
                            if index:
                                self.assertAlmostEqual(
                                    (bounds.top - pins[index - 1].bounds.top) / units,
                                    1.27,
                                )
                        else:
                            self.assertEqual(bounds.left, body.right)
                            if index > rows:
                                self.assertLess(bounds.top, pins[index - 1].bounds.top)
                        self.assertGreater(bounds.top, body.top)
                        self.assertLess(bounds.bottom, body.bottom)
                        self.assertAlmostEqual((bounds.bottom - bounds.top) / units,
                                               0.41)
                        number = renderer.pin_number_bounds(pin, layout)
                        gap = (bounds.left - number.right if is_left
                               else number.left - bounds.right)
                        self.assertAlmostEqual(gap, PIN_NUMBER_GAP)
                        self.assertGreater(number.left, 0)
                        self.assertLess(number.right, orientation.value[0])
                        self.assertGreater(number.top, 0)
                        self.assertLess(number.bottom, orientation.value[1])
                    self.assertAlmostEqual(
                        (pins[-1].bounds.right - pins[0].bounds.left) / units, 6.0
                    )
                    self.assertGreater(body.top, 0)
                    self.assertLess(body.bottom, orientation.value[1])

    def test_fixed_references_preserve_source_precision(self) -> None:
        expected = {
            8: (("0.150-0.157", "3.81-3.98"), ("0.189-0.197", "4.81-5.00"),
                ("0.228-0.244", "5.80-6.19"), ("0.050", "1.27")),
            14: (("0.1496-0.1575", "3.8-4.0"), ("0.3366-0.3445", "8.55-8.75"),
                 ("0.2283-0.2441", "5.8-6.2"), ("0.0500", "1.27")),
            16: (("0.1496-0.1575", "3.8-4.0"), ("0.3858-0.3937", "9.8-10.0"),
                 ("0.2283-0.2441", "5.8-6.2"), ("0.0500", "1.27")),
        }
        for count, values in expected.items():
            rows = SoicRenderer(count).reference_dimensions
            self.assertEqual(tuple((row.inches, row.millimeters) for row in rows),
                             values)
            self.assertEqual(tuple(row.label for row in rows),
                             ("Body width", "Body length", "Lead span", "Pin pitch"))

    def test_marker_has_equal_insets_and_dip_sized_dot(self) -> None:
        for count in SUPPORTED_PIN_COUNTS:
            renderer = SoicRenderer(count)
            for orientation in Orientation:
                body = renderer.package_layout(orientation).body
                svg = renderer.render("EXAMPLE", orientation).to_string()
                root = ET.fromstring(svg)
                dot = root.find(f".//{_SVG}ellipse")
                self.assertAlmostEqual(float(dot.get("cx")) - body.left, 70.5)
                self.assertAlmostEqual(float(dot.get("cy")) - body.top, 70.5)
                self.assertAlmostEqual(float(dot.get("rx")) * 2, 57)
                self.assertAlmostEqual(float(dot.get("ry")) * 2, 57)

    def test_invalid_counts_names_and_annotations_are_reported(self) -> None:
        for count in (True, 8.0, "8", 0, 6, 12, 20, 24):
            with self.subTest(count=count), self.assertRaises(ValueError):
                SoicRenderer(count)
        renderer = SoicRenderer()
        for name in ("", "   ", "two\nlines", "X" * 200):
            with self.subTest(name=name), self.assertRaises(ValueError):
                renderer.render(name)
        with self.assertRaises(TypeError):
            renderer.package_layout("landscape")
        plugin = get_package("SOIC")
        with self.assertRaisesRegex(ValueError, "cannot fit"):
            plugin.pinout_factory(renderer).render("TEST", {1: PinLabel("X" * 200)})

    def test_catalog_checks_geometry_and_assets(self) -> None:
        data = json.loads((_DIRECTORY / "variants/soic8.json").read_text("utf-8"))
        mutations = (
            {"pin_count": 12},
            {"pin_count": 8.0},
            {"geometry_mm": {**data["geometry_mm"], "span": 3.9}},
            {"geometry_mm": {**data["geometry_mm"], "length": 3.0}},
            {"geometry_mm": {**data["geometry_mm"], "width": 0}},
            {"geometry_mm": {**data["geometry_mm"], "pitch": float("nan")}},
            {"geometry_mm": {**data["geometry_mm"], "span": float("inf")}},
            {"geometry_mm": {**data["geometry_mm"], "lead_width": 1.27}},
            {"reference": {}},
            {"source": ""},
        )
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "No SOIC variant"):
                load_variants(directory)
            path = Path(directory) / "variant.json"
            for mutation in mutations:
                with self.subTest(mutation=mutation):
                    path.write_text(json.dumps({**data, **mutation}), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_variants(directory)
            path.write_text(json.dumps(data), encoding="utf-8")
            (Path(directory) / "duplicate.json").write_text(json.dumps(data),
                                                          encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate SOIC"):
                load_variants(directory)

    def test_sample_discovery_completeness_and_repeatability(self) -> None:
        plugin = get_package("SOIC")
        self.assertEqual(plugin.pin_counts, (8, 14, 16))
        with TemporaryDirectory() as directory:
            paths = generate_package_samples(plugin, directory)
            self.assertEqual(len(paths), 6)
            original = {path: path.read_bytes() for path in paths}
            for path in paths:
                root = ET.parse(path).getroot()
                stored = ET.parse(_DIRECTORY / "samples" / path.name).getroot()
                self.assertEqual(ET.tostring(root), ET.tostring(stored))
                count = int(path.stem.split("-")[0].removeprefix("soic"))
                orientation = (Orientation.LANDSCAPE if "landscape" in path.stem
                               else Orientation.PORTRAIT)
                width, height = orientation.value
                self.assertEqual(root.get("viewBox"), f"0 0 {width} {height}")
                self.assertEqual(len(root.findall(f".//{_SVG}polygon")), count)
                labels = [group.get("aria-label") for group in
                          root.findall(f".//{_SVG}g[@aria-label]")]
                self.assertEqual(labels[:count], [str(n) for n in range(1, count + 1)])
                self.assertIn(f"SOIC-{count}", labels)
                self.assertFalse(root.findall(f".//{_SVG}image"))
                self.assertFalse(root.findall(f".//{_SVG}text"))
            generate_package_samples(plugin, directory)
            self.assertEqual(original, {path: path.read_bytes() for path in paths})

    def test_json_input_badges_and_color_overrides(self) -> None:
        for count in SUPPORTED_PIN_COUNTS:
            for orientation in Orientation:
                data = {
                    "name": "EXAMPLE",
                    "package": {"family": "SOIC", "pin_count": count},
                    "orientation": orientation.name.lower(),
                    "content_scale": 0.5,
                    "categories": {"io": {"name": "Signals", "color": "#123456"}},
                    "pins": [{"number": number, "type": "io", "definitions": [
                        {"column": 1, "category": "io", "name": f"P{number}"}
                    ]} for number in range(1, count + 1)],
                }
                original = deepcopy(data)
                request = parse_input(data)
                svg = request.render().to_string()
                self.assertEqual(svg, request.render().to_string())
                self.assertEqual(data, original)
                root = ET.fromstring(svg)
                labels = [group.get("aria-label") for group in
                          root.findall(f".//{_SVG}g[@aria-label]")]
                self.assertEqual(labels.count("I/O"), count)
                for number in range(1, count + 1):
                    self.assertIn(f"P{number}", labels)
                self.assertIn("#123456", svg)


if __name__ == "__main__":
    unittest.main()
