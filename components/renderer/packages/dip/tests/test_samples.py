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

"""Generate and validate every supported DIP sample in both orientations."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET

from components.renderer import Orientation
from components.renderer.packages.dip import SUPPORTED_PIN_COUNTS
from components.renderer.packages.registry import get_package
from components.renderer.packages.samples import generate_package_samples


_SVG = "{http://www.w3.org/2000/svg}"


class DipSampleTests(unittest.TestCase):
    """Check every supported pin count, physical numbers, and repeatable output."""

    def test_generate_every_supported_package_and_orientation(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "samples"
            plugin = get_package("DIP")
            paths = generate_package_samples(plugin, output)
            expected = {
                f"dip{count}-{orientation.name.lower()}.svg": (count, orientation)
                for count in SUPPORTED_PIN_COUNTS
                for orientation in Orientation
            }
            self.assertEqual(len(paths), len(expected))
            self.assertEqual({path.name for path in output.iterdir()}, set(expected))
            contents = {path.name: path.read_bytes() for path in paths}
            for path in paths:
                with self.subTest(sample=path.name):
                    self.assertEqual(path.parent, output)
                    count, orientation = expected[path.name]
                    root = ET.fromstring(contents[path.name])
                    width, height = orientation.value
                    self.assertEqual(root.get("viewBox"), f"0 0 {width} {height}")
                    self.assertEqual(root.get("width"), str(width))
                    self.assertEqual(root.get("height"), str(height))
                    self.assertEqual(len(root.findall(f".//{_SVG}polygon")), count)
                    labels = [
                        group.get("aria-label")
                        for group in root.findall(f".//{_SVG}g[@aria-label]")
                    ]
                    numbers = [label for label in labels if label.isdecimal()]
                    self.assertEqual(numbers, [str(n) for n in range(1, count + 1)])
                    self.assertIn("EXAMPLE", labels)
                    self.assertIn(f"DIP-{count}", labels)
                    self.assertFalse(root.findall(f".//{_SVG}image"))

            self.assertEqual(generate_package_samples(plugin, output), paths)
            self.assertEqual(
                {path.name: path.read_bytes() for path in paths}, contents
            )


if __name__ == "__main__":
    unittest.main()
