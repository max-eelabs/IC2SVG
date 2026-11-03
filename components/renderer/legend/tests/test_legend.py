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

"""Check the standard legend's column limit, placement, and independent scale."""

import unittest
from xml.etree import ElementTree as ET

from components.renderer import (
    LegendEntry, LegendRenderer, PinLabel, SvgDocument, TopRightLegendRenderer,
)


_SVG = "{http://www.w3.org/2000/svg}"


class LegendTests(unittest.TestCase):
    """Keep every entry visible and cap each legend column at four items."""

    def test_column_boundaries_and_no_outer_border(self) -> None:
        for count in (1, 4, 5, 8, 9, 12, 13):
            with self.subTest(count=count):
                document = SvgDocument((1920, 1080), content_scale=0.35)
                entries = [
                    LegendEntry(PinLabel(f"P{index}"), f"Category {index}")
                    for index in range(count)
                ]
                bounds = TopRightLegendRenderer().render(document, entries)
                self.assertEqual(bounds.top, 32)
                self.assertEqual(bounds.right, 1920 - 32)
                self.assertGreater(bounds.left, 0)
                self.assertLess(bounds.bottom, 1080)
                root = ET.fromstring(document.to_string())
                legend = root.find(f"{_SVG}g[@id='legend']")
                boxes = legend.findall(f"{_SVG}rect")
                self.assertEqual(len(boxes), count)
                columns: dict[str, list[ET.Element]] = {}
                for box in boxes:
                    columns.setdefault(box.get("x"), []).append(box)
                self.assertEqual(len(columns), (count + 3) // 4)
                self.assertTrue(all(len(column) <= 4 for column in columns.values()))
                if count > 4:
                    self.assertEqual(boxes[0].get("y"), boxes[4].get("y"))

    def test_scale_independence_and_definition_style(self) -> None:
        entries = [LegendEntry(PinLabel("~RESET", "#FDD835"), "Reset")]
        blocks = []
        for scale in (0.2, 0.6, 1.0):
            document = SvgDocument((1080, 1920), content_scale=scale)
            blocks.append(TopRightLegendRenderer().render(document, entries))
            root = ET.fromstring(document.to_string())
            legend = root.find(f"{_SVG}g[@id='legend']")
            self.assertEqual(len(legend.findall(f"{_SVG}line")), 1)
            self.assertIsNotNone(legend.find(f"{_SVG}g[@aria-label='RESET']"))
        self.assertEqual(blocks[0], blocks[1])
        self.assertEqual(blocks[1], blocks[2])
        with self.assertRaises(TypeError):
            LegendRenderer()

    def test_color_variants_share_one_split_swatch(self) -> None:
        entry = LegendEntry(
            PinLabel("VCC", "#E53935", "#FFFFFF"), "Power",
            (PinLabel("GND", "#202020", "#FFFFFF"),),
        )
        document = SvgDocument((1920, 1080))
        TopRightLegendRenderer().render(document, [entry])
        original = document.to_string()
        root = ET.fromstring(original)
        legend = root.find(f"{_SVG}g[@id='legend']")
        self.assertEqual(len(legend.findall(f"{_SVG}rect")), 1)
        bands = legend.find(f"{_SVG}g[@clip-path]")
        self.assertEqual(
            [path.get("fill") for path in bands.findall(f"{_SVG}path")],
            ["#E53935", "#202020"],
        )
        self.assertIsNotNone(root.find(f".//{_SVG}clipPath"))
        self.assertIsNotNone(legend.find(f"{_SVG}g[@aria-label='VCC/GND']"))
        descriptions = legend.findall(f"{_SVG}g[@aria-label='Power']")
        self.assertEqual(len(descriptions), 1)
        # Fill overrides must not leak into subsequent drawing operations.
        document.rounded_rectangle(
            (100, 100, 200, 150), radius=5, fill="#E53935", outline="#202020", width=1
        )
        root = ET.fromstring(document.to_string())
        self.assertEqual(root.findall(f"{_SVG}rect")[-1].get("fill"), "#E53935")


if __name__ == "__main__":
    unittest.main()
