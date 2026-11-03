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

"""Check nominal measurements and consistent sheet overlay typography."""

import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from components.renderer import (
    DipRenderer, LegendEntry, Orientation, PinLabel, SvgDocument,
    TopLeftPackageRenderer, TopRightLegendRenderer,
)


_SVG = "{http://www.w3.org/2000/svg}"


class PackageInfoTests(unittest.TestCase):
    """Keep physical dimensions distinct from illustration and export scaling."""

    def test_nominal_dimensions_and_sheet_placement(self) -> None:
        overlays = []
        for orientation in Orientation:
            for scale in (0.1, 0.2):
                document = SvgDocument(orientation.value, content_scale=scale)
                TopLeftPackageRenderer().render(document, DipRenderer(8))
                svg = document.to_string()
                repeated = SvgDocument(orientation.value, content_scale=scale)
                TopLeftPackageRenderer().render(repeated, DipRenderer(8))
                self.assertEqual(svg, repeated.to_string())
                root = ET.fromstring(svg)
                block = root.find(f"{_SVG}g[@id='package-info']")
                self.assertEqual(block.get("transform"), "translate(32 32) scale(1)")
                self.assertEqual(
                    [group.get("aria-label") for group in block],
                    ["Package", "Body width: 0.250 in (6.35 mm)",
                     "Body length: 0.373 in (9.46 mm)",
                     "Lead span: 0.370 in (9.40 mm)",
                     "Pin pitch: 0.100 in (2.54 mm)"],
                )
                overlays.append(ET.tostring(block))
        self.assertTrue(all(block == overlays[0] for block in overlays))
        self.assertEqual(
            DipRenderer(24).nominal_dimensions_mm, (13.84, 31.75, 16.51, 2.54)
        )

    def test_heading_and_visible_gap_match_legend(self) -> None:
        document = SvgDocument((1920, 1080))
        with patch.object(document, "text", wraps=document.text) as draw:
            TopLeftPackageRenderer().render(document, DipRenderer(8))
            heading, first_line = draw.call_args_list[:2]
            heading_bounds = document.text_bounds(*heading.args, **{
                key: value for key, value in heading.kwargs.items() if key != "fill"
            })
            line_bounds = document.text_bounds(*first_line.args, **{
                key: value for key, value in first_line.kwargs.items() if key != "fill"
            })
            self.assertAlmostEqual(line_bounds[1] - heading_bounds[3], 12)

        with patch.object(document, "text", wraps=document.text) as draw:
            TopRightLegendRenderer().render(
                document, [LegendEntry(PinLabel("VCC"), "Power")]
            )
            legend_heading = draw.call_args_list[0]
            self.assertAlmostEqual(
                heading.kwargs["font"].size,
                legend_heading.kwargs["font"].size * 0.35,
            )
            self.assertAlmostEqual(heading.args[0][1], legend_heading.args[0][1] * 0.35)
            self.assertEqual(heading.kwargs["bold"], legend_heading.kwargs["bold"])


if __name__ == "__main__":
    unittest.main()
