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

"""Behavior checks for the rendering contract and DIP-6 output."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

from components.renderer import DipRenderer, IcRenderer, Orientation


_SVG = "{http://www.w3.org/2000/svg}"


class DipRendererTests(unittest.TestCase):
    """Validate vector output, physical numbering, and reproducible SVG."""

    def test_base_renderer_is_abstract(self) -> None:
        with self.assertRaises(TypeError):
            IcRenderer()

    def test_exact_sizes_and_repeatable_vectors(self) -> None:
        renderer = DipRenderer()
        for orientation in Orientation:
            with self.subTest(orientation=orientation):
                document = renderer.render("TEST-IC", orientation)
                self.assertEqual(document.size, orientation.value)
                svg = document.to_string()
                self.assertEqual(
                    svg, renderer.render("TEST-IC", orientation).to_string()
                )
                root = ET.fromstring(svg)
                width, height = orientation.value
                self.assertEqual(root.get("viewBox"), f"0 0 {width} {height}")
                self.assertEqual(root.get("width"), str(width))
                self.assertEqual(root.get("height"), str(height))
                self.assertEqual(len(root.findall(f".//{_SVG}polygon")), 6)
                self.assertTrue(root.findall(f".//{_SVG}path"))
                self.assertFalse(root.findall(f".//{_SVG}image"))
                self.assertFalse(root.findall(f".//{_SVG}text"))

    def test_scaling_preserves_geometry_and_colors(self) -> None:
        document = DipRenderer().render("TEST-IC")
        original = document.to_string()
        root = ET.fromstring(original)
        scaled = ET.fromstring(document.to_string(scale=4))
        self.assertEqual(scaled.get("width"), "7680")
        self.assertEqual(scaled.get("height"), "4320")
        self.assertEqual(scaled.get("viewBox"), root.get("viewBox"))
        self.assertEqual(
            [ET.tostring(child) for child in root],
            [ET.tostring(child) for child in scaled],
        )
        self.assertEqual(document.to_string(), original)
        with TemporaryDirectory() as directory:
            path = Path(directory) / "dip6.svg"
            document.save(path, scale=4)
            self.assertEqual(
                path.read_text(encoding="utf-8"), document.to_string(scale=4)
            )

    def test_pin_one_marker_and_palette(self) -> None:
        renderer = DipRenderer()
        root = ET.fromstring(renderer.render("TEST-IC").to_string())
        body = renderer.package_layout(Orientation.LANDSCAPE).body
        marker = root.find(f".//{_SVG}ellipse")
        self.assertIsNotNone(marker)
        self.assertEqual(float(marker.get("rx")), 28.5)
        self.assertEqual(float(marker.get("ry")), 28.5)
        self.assertAlmostEqual(float(marker.get("cx")) - 28.5 - body.left, 42)
        self.assertAlmostEqual(float(marker.get("cy")) - 28.5 - body.top, 42)
        colors = {
            element.get(attribute)
            for element in root.iter()
            for attribute in ("fill", "stroke")
            if element.get(attribute)
        }
        self.assertEqual(
            colors,
            {
                "white", "#A6ABB0", "#646A70", "#E4E7EA", "#333333",
                "#202226", "#151619", "#33363B", "#4B4F55", "#16181B",
                "#55595F", "#656A71", "#F2F2F2",
            },
        )

    def test_label_escaping_and_outlines(self) -> None:
        root = ET.fromstring(DipRenderer().render("A&B <1>").to_string())
        labels = root.findall(f".//{_SVG}g[@aria-label]")
        self.assertIn("A&B <1>", [label.get("aria-label") for label in labels])
        for label in labels:
            self.assertTrue(label.findall(f".//{_SVG}path"))

    def test_top_view_numbering_and_bounds(self) -> None:
        renderer = DipRenderer()
        for orientation in Orientation:
            layout = renderer.package_layout(orientation)
            pins = layout.pins
            self.assertEqual([pin.number for pin in pins], [1, 2, 3, 4, 5, 6])
            self.assertLess(pins[0].bounds.top, pins[1].bounds.top)
            self.assertLess(pins[1].bounds.top, pins[2].bounds.top)
            self.assertGreater(pins[3].bounds.top, pins[4].bounds.top)
            self.assertGreater(pins[4].bounds.top, pins[5].bounds.top)
            self.assertLess(pins[0].bounds.left, layout.body.left)
            self.assertGreater(pins[5].bounds.right, layout.body.right)
            for pin in pins:
                self.assertGreaterEqual(pin.bounds.left, 0)
                self.assertGreaterEqual(pin.bounds.top, 0)
                self.assertLess(pin.bounds.right, orientation.value[0])
                self.assertLess(pin.bounds.bottom, orientation.value[1])

    def test_invalid_inputs(self) -> None:
        for count in (0, 5, 10, 12, 22, 32, 6.0, True, "8"):
            with self.subTest(count=count), self.assertRaises(ValueError):
                DipRenderer(count)

        renderer = DipRenderer()
        for name in ("", "   ", "two\nlines", "X" * 200):
            with self.subTest(name=name), self.assertRaises(ValueError):
                renderer.render(name)
        with self.assertRaises(TypeError):
            renderer.render("TEST", "landscape")
        with self.assertRaises(ValueError):
            renderer.render("TEST \U0001f600")
        for scale in (0, -1, float("nan"), float("inf")):
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                renderer.render("TEST").to_string(scale=scale)

    def test_dip6_outline_proportions(self) -> None:
        """Check physical ratios against Vishay outline 83253, not pixel offsets."""
        for orientation in Orientation:
            layout = DipRenderer().package_layout(orientation)
            body = layout.body
            scale = (body.right - body.left) / 6.4
            self.assertAlmostEqual((body.bottom - body.top) / scale, 8.6)
            self.assertAlmostEqual(
                (layout.pins[1].bounds.top - layout.pins[0].bounds.top) / scale,
                2.54,
            )
            lead = layout.pins[0].bounds
            self.assertAlmostEqual((lead.bottom - lead.top) / scale, 1.27)
            span_mm = (layout.pins[5].bounds.right - lead.left) / scale
            nominal_span = (7.62 + 8.81) / 2
            self.assertAlmostEqual(span_mm, 6.4 + (nominal_span - 6.4) * 0.765)

    def test_shorter_pins_remove_only_wide_section_length(self) -> None:
        """The tip moves inward; the taper and narrow tip retain their lengths."""
        for orientation in Orientation:
            renderer = DipRenderer(8)
            layout = renderer.package_layout(orientation)
            units = (layout.body.right - layout.body.left) / 6.35
            original_length = (9.40 - 6.35) * units / 2
            root = ET.fromstring(renderer.render("TEST", orientation).to_string())
            polygon = root.find(f".//{_SVG}polygon")
            points = [
                tuple(float(value) for value in point.split(","))
                for point in polygon.get("points").split()
            ]
            pin_root, wide_end, taper_end, tip = [point[0] for point in points[:4]]
            self.assertAlmostEqual(
                pin_root - tip, original_length * 0.765, places=5
            )
            self.assertAlmostEqual(
                pin_root - wide_end, original_length * 0.315, places=5
            )
            self.assertAlmostEqual(taper_end - tip, 0.20 * units, places=5)
            self.assertAlmostEqual(
                wide_end - taper_end, original_length * 0.45 - 0.20 * units,
                places=5,
            )

    def test_all_supported_pin_counts(self) -> None:
        """Every package fits both canvases and numbers both rows correctly."""
        for count in (4, 6, 8, 14, 16, 18, 20, 24, 28):
            renderer = DipRenderer(count)
            rows = count // 2
            for orientation in Orientation:
                with self.subTest(count=count, orientation=orientation):
                    layout = renderer.package_layout(orientation)
                    pins = layout.pins
                    self.assertEqual(renderer.pin_count, count)
                    self.assertEqual(
                        [pin.number for pin in pins], list(range(1, count + 1))
                    )
                    self.assertEqual(pins[0].bounds.top, pins[-1].bounds.top)
                    self.assertEqual(pins[rows - 1].bounds.top, pins[rows].bounds.top)
                    for pin in pins[:rows]:
                        self.assertEqual(pin.bounds.right, layout.body.left)
                    for pin in pins[rows:]:
                        self.assertEqual(pin.bounds.left, layout.body.right)
                    for pin in pins:
                        self.assertGreater(pin.bounds.left, 0)
                        self.assertGreater(pin.bounds.top, 0)
                        self.assertLess(pin.bounds.right, orientation.value[0])
                        self.assertLess(pin.bounds.bottom, orientation.value[1])
                    self.assertGreater(layout.body.top, 0)
                    self.assertLess(layout.body.bottom, orientation.value[1])
                    self.assertLess(pins[rows - 1].bounds.bottom, layout.body.bottom)
                    self.assertGreater(pins[0].bounds.top, layout.body.top)

                    svg = renderer.render("EXAMPLE", orientation).to_string()
                    self.assertEqual(
                        svg, renderer.render("EXAMPLE", orientation).to_string()
                    )
                    root = ET.fromstring(svg)
                    self.assertEqual(len(root.findall(f".//{_SVG}polygon")), count)
                    labels = [
                        g.get("aria-label")
                        for g in root.findall(f".//{_SVG}g[@aria-label]")
                    ]
                    self.assertEqual(
                        labels[:count], [str(n) for n in range(1, count + 1)]
                    )
                    self.assertIn(f"DIP-{count}", labels)
                    self.assertFalse(root.findall(f".//{_SVG}image"))

    def test_fitting_keeps_physical_ratios(self) -> None:
        """Changing orientation changes scale uniformly, including marker details."""
        for count in (4, 6, 8, 14, 16, 18, 20, 24, 28):
            renderer = DipRenderer(count)
            layouts = [renderer.package_layout(o) for o in Orientation]
            widths = [p.body.right - p.body.left for p in layouts]
            ratio = widths[1] / widths[0]
            heights = [p.body.bottom - p.body.top for p in layouts]
            self.assertAlmostEqual(heights[1] / heights[0], ratio)
            pitches = [p.pins[1].bounds.top - p.pins[0].bounds.top for p in layouts]
            self.assertAlmostEqual(pitches[1] / pitches[0], ratio)
            markers = [
                ET.fromstring(renderer.render("EXAMPLE", o).to_string())
                .find(f".//{_SVG}ellipse")
                for o in Orientation
            ]
            self.assertAlmostEqual(
                float(markers[1].get("rx")) / float(markers[0].get("rx")),
                ratio,
                places=5,
            )

    def test_end_pin_clearance(self) -> None:
        """End shoulders have equal visible clearance without compressing pitch."""
        widths_mm = {
            4: 6.50, 6: 6.40, 8: 6.35, 14: 6.35, 16: 6.35,
            18: 6.35, 20: 6.35, 24: 13.84, 28: 7.24,
        }
        for count, width_mm in widths_mm.items():
            for orientation in Orientation:
                with self.subTest(count=count, orientation=orientation):
                    layout = DipRenderer(count).package_layout(orientation)
                    units = (layout.body.right - layout.body.left) / width_mm
                    top_gap = layout.pins[0].bounds.top - layout.body.top
                    bottom_gap = (
                        layout.body.bottom - layout.pins[count // 2 - 1].bounds.bottom
                    )
                    self.assertGreaterEqual(top_gap / units, 0.75 - 1e-9)
                    self.assertAlmostEqual(top_gap, bottom_gap)
                    centers = [
                        (pin.bounds.top + pin.bounds.bottom) / 2
                        for pin in layout.pins[:count // 2]
                    ]
                    for upper, lower in zip(centers, centers[1:]):
                        self.assertAlmostEqual((lower - upper) / units, 2.54)


if __name__ == "__main__":
    unittest.main()
