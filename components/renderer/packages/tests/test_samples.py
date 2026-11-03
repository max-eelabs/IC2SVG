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

"""Generate and verify SVG samples for every discovered package family."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET

from components.renderer import Orientation
from components.renderer.packages.registry import discover_packages
from components.renderer.packages.samples import generate_all_samples


_SVG = "{http://www.w3.org/2000/svg}"


class PackageSampleTests(unittest.TestCase):
    """Verify complete, repeatable exports without changing repository artifacts."""

    def test_generate_all_discovered_package_families(self) -> None:
        plugins = discover_packages()
        self.assertTrue(plugins)
        with TemporaryDirectory() as directory:
            paths = generate_all_samples(directory)
            expected = {
                Path(directory) / plugin.family.lower()
                / f"{plugin.family.lower()}{count}-{orientation.name.lower()}.svg":
                (count, orientation)
                for plugin in plugins
                for count in plugin.pin_counts
                for orientation in Orientation
            }
            self.assertEqual(set(paths), set(expected))
            original = {path: path.read_bytes() for path in paths}
            for path, (count, orientation) in expected.items():
                with self.subTest(sample=str(path)):
                    root = ET.fromstring(original[path])
                    width, height = orientation.value
                    self.assertEqual(root.get("viewBox"), f"0 0 {width} {height}")
                    numbers = [
                        group.get("aria-label")
                        for group in root.findall(f".//{_SVG}g[@aria-label]")
                        if group.get("aria-label").isdecimal()
                    ]
                    self.assertEqual(numbers, [str(n) for n in range(1, count + 1)])
                    self.assertFalse(root.findall(f".//{_SVG}image"))
            self.assertEqual(generate_all_samples(directory), paths)
            self.assertEqual({path: path.read_bytes() for path in paths}, original)


if __name__ == "__main__":
    unittest.main()
