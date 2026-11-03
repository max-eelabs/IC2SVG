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

"""Protect published DIP reference values independently of drawing geometry."""

import unittest
from unittest.mock import PropertyMock, patch
from xml.etree import ElementTree as ET

from components.renderer import DipRenderer, SvgDocument, TopLeftPackageRenderer
from components.renderer.packages.dip.specifications import dip_specification


_SVG = "{http://www.w3.org/2000/svg}"


class DipSpecificationTests(unittest.TestCase):
    """Preserve source ranges and precision in the selected package's reference rows."""

    def test_dip6_and_dip14_use_published_values(self) -> None:
        expected = {
            6: [
                "Package",
                "Body width: 0.248-0.256 in (6.30-6.50 mm)",
                "Body length: 0.335-0.343 in (8.50-8.70 mm)",
                "Lead span: 0.300-0.347 in (7.62-8.81 mm)",
                "Pin pitch: 0.100 in (2.54 mm)",
            ],
            14: [
                "Package",
                "Body width: 0.250 in (6.35 mm)",
                "Body length: 0.750 in (19.05 mm)",
                "Lead span: 0.370 in (9.40 mm)",
                "Pin pitch: 0.100 in (2.54 mm)",
            ],
        }
        for count, labels in expected.items():
            with self.subTest(pin_count=count):
                package = DipRenderer(count)
                # Illustration changes must never change the published values.
                document = SvgDocument((1080, 1920))
                with patch.object(
                    DipRenderer, "nominal_dimensions_mm", new_callable=PropertyMock,
                    side_effect=AssertionError("Illustration dimensions were accessed"),
                ):
                    bounds = TopLeftPackageRenderer().render(document, package)
                root = ET.fromstring(document.to_string())
                block = root.find(f"{_SVG}g[@id='package-info']")
                self.assertEqual([g.get("aria-label") for g in block], labels)
                self.assertLess(bounds.right, 483)  # Standard portrait legend left.

    def test_every_supported_outline_has_a_reference(self) -> None:
        for count in (4, 6, 8, 14, 16, 18, 20, 24, 28):
            with self.subTest(pin_count=count):
                reference = dip_specification(count)
                self.assertTrue(reference.source.startswith("https://"))
                self.assertEqual(reference.pin_pitch.inches, "0.100")
                self.assertEqual(reference.pin_pitch.millimeters, "2.54")
                TopLeftPackageRenderer().render(
                    SvgDocument((1080, 1920)), DipRenderer(count)
                )
        # Preserve the source's inch value rather than reconverting rounded mm.
        self.assertEqual(dip_specification(8).body_length.inches, "0.373")
        with self.assertRaisesRegex(ValueError, "No reference dimensions"):
            dip_specification(10)


if __name__ == "__main__":
    unittest.main()
