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

"""Check active-low notation and the resulting visible SVG overbars."""

import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from PIL import ImageFont

from components.renderer import PinLabel, Rectangle, RoundedDefinitionRenderer
from components.renderer import SvgDocument
from components.renderer.definition.text import parse_signal_text


_SVG = "{http://www.w3.org/2000/svg}"


class SignalTextTests(unittest.TestCase):
    """Verify bars cover only marked signal names and remain inside the box."""

    def test_signal_ranges(self) -> None:
        cases = (
            ("~RESET/dW", "RESET/dW", ((0, 5),)),
            ("OC0A/~OC1A", "OC0A/OC1A", ((5, 9),)),
            ("~A/~B", "A/B", ((0, 1), (2, 3))),
            ("~RESET dW", "RESET dW", ((0, 5),)),
            ("VCC", "VCC", ()),
        )
        for source, text, ranges in cases:
            with self.subTest(source=source):
                parsed = parse_signal_text(source)
                self.assertEqual(parsed.text, text)
                self.assertEqual(parsed.overbars, ranges)
        for invalid in ("~", "A/~", "~ A", "~~RESET"):
            with self.assertRaises(ValueError):
                parse_signal_text(invalid)

    def test_uniform_definition_scaling_preserves_decoration(self) -> None:
        label = PinLabel("~RESET")
        baseline = RoundedDefinitionRenderer().measure(label)
        scaled = RoundedDefinitionRenderer(scale=0.9)
        size = scaled.measure(label)
        self.assertAlmostEqual(size.width, baseline.width * 0.9)
        self.assertAlmostEqual(size.height, baseline.height * 0.9)
        document = SvgDocument((1920, 1080))
        with patch.object(document, "text", wraps=document.text) as draw:
            scaled.render(document, label, Rectangle(0, 0, size.width, size.height))
        self.assertAlmostEqual(draw.call_args.kwargs["font"].size, 28 * 1.716 * 0.9)
        root = ET.fromstring(document.to_string())
        self.assertEqual(len(root.findall(f"{_SVG}line")), 1)
        for invalid in (0, -1, float("nan"), float("inf")):
            with self.subTest(scale=invalid), self.assertRaises(ValueError):
                RoundedDefinitionRenderer(scale=invalid)

    def test_measurement_omits_tilde(self) -> None:
        renderer = RoundedDefinitionRenderer()
        self.assertEqual(renderer.measure(PinLabel("~RESET")),
                         renderer.measure(PinLabel("RESET")))
        self.assertEqual(renderer.measure(PinLabel("OC0A/~OC1A")),
                         renderer.measure(PinLabel("OC0A/OC1A")))

    def test_bar_geometry_and_plain_text(self) -> None:
        renderer = RoundedDefinitionRenderer()
        font = ImageFont.load_default(size=28 * 1.716)
        for source in ("~RESET/dW", "OC0A/~OC1A", "~A/~B", "VCC"):
            with self.subTest(source=source):
                label = PinLabel(source, "#202020", "#FFFFFF")
                size = renderer.measure(label)
                box = Rectangle(100, 100, 100 + size.width, 100 + size.height)
                document = SvgDocument((800, 400))
                renderer.render(document, label, box)
                root = ET.fromstring(document.to_string())
                parsed = parse_signal_text(source)
                group = root.find(f"{_SVG}g")
                self.assertEqual(group.get("aria-label"), parsed.text)
                bars = root.findall(f"{_SVG}line")
                self.assertEqual(len(bars), len(parsed.overbars))
                origin = (box.left + box.right) / 2 - font.getlength(parsed.text) / 2
                cy = (box.top + box.bottom) / 2
                for bar, (start, end) in zip(bars, parsed.overbars):
                    offset = font.getlength(parsed.text[:start + 1])
                    offset -= font.getlength(parsed.text[start])
                    ink = document.text_bounds(
                        (origin + offset, cy), parsed.text[start:end],
                        font=font, anchor="lm", bold=True,
                    )
                    self.assertAlmostEqual(float(bar.get("x1")), ink[0], places=5)
                    self.assertAlmostEqual(float(bar.get("x2")), ink[2], places=5)
                    self.assertLess(float(bar.get("y1")), ink[1])
                    self.assertGreater(float(bar.get("y1")), box.top)
                    self.assertEqual(bar.get("y1"), bar.get("y2"))
                    self.assertEqual(bar.get("stroke"), label.text_color)


if __name__ == "__main__":
    unittest.main()
