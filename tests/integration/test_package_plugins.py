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

"""Prove new package folders work without editing loader, schema, or generators."""

from collections.abc import Generator
from contextlib import contextmanager
from importlib import invalidate_caches
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from components.input import parse_input
from components.renderer import Orientation
from components.renderer import packages
from components.renderer.packages.registry import discover_packages, get_package
from components.renderer.packages.samples import generate_all_samples


_SVG = "{http://www.w3.org/2000/svg}"


@contextmanager
def _added_package(plugin_fixture: str | None = None) -> Generator[Path, None, None]:
    """Add a package folder on a temporary namespace path, then restore imports."""
    fixtures = Path(__file__).with_name("fixtures")
    fixture = fixtures / "package_addon"
    prefix = "components.renderer.packages.package_addon"
    with TemporaryDirectory() as directory:
        destination = Path(directory) / "package_addon"
        shutil.copytree(
            fixture, destination, ignore=shutil.ignore_patterns("__pycache__")
        )
        if plugin_fixture is not None:
            shutil.copyfile(
                fixtures / "plugin_declarations" / plugin_fixture,
                destination / "plugin.py",
            )
        with patch.object(packages, "__path__", [*packages.__path__, directory]):
            invalidate_caches()
            try:
                yield destination
            finally:
                for module in tuple(sys.modules):
                    if module == prefix or module.startswith(prefix + "."):
                        del sys.modules[module]
                if hasattr(packages, "package_addon"):
                    delattr(packages, "package_addon")
                invalidate_caches()


class PackagePluginTests(unittest.TestCase):
    """Exercise discovery, complete JSON rendering, and samples for an added family."""

    def test_added_folder_supports_new_family_counts_and_reference_rows(self) -> None:
        original_families = tuple(plugin.family for plugin in discover_packages())
        with _added_package():
            self.assertIn(
                "TEST_ADDON", [plugin.family for plugin in discover_packages()]
            )
            for count in (2, 32):
                data = {
                    "name": "NEW-IC",
                    "package": {"family": "TEST_ADDON", "pin_count": count},
                    "categories": {},
                    "pins": [
                        {"number": number, "type": "nc", "definitions": []}
                        for number in range(1, count + 1)
                    ],
                }
                for orientation in Orientation:
                    with self.subTest(count=count, orientation=orientation):
                        data["orientation"] = orientation.name.lower()
                        pinout = parse_input(data)
                        self.assertEqual(pinout.family, "TEST_ADDON")
                        svg = pinout.render().to_string()
                        root = ET.fromstring(svg)
                        self.assertEqual(pinout.render().to_string(), svg)
                        self.assertIsNotNone(root.find(f"{_SVG}g[@id='addon-pinout']"))
                        block = root.find(f"{_SVG}g[@id='package-info']")
                        self.assertEqual(
                            [group.get("aria-label") for group in block],
                            ["Package", "Test pitch: 0.100 in (2.54 mm)"],
                        )
                        self.assertEqual(len(root.findall(
                            f".//{_SVG}g[@aria-label='NC']"
                        )), count)
        self.assertEqual(
            tuple(plugin.family for plugin in discover_packages()), original_families
        )

    def test_new_family_samples_are_discovered_without_generator_changes(self) -> None:
        with _added_package() as package_path, TemporaryDirectory() as output:
            paths = generate_all_samples(output)
            addon_paths = [path for path in paths if path.parent.name == "test_addon"]
            self.assertEqual(
                {path.name for path in addon_paths},
                {f"test_addon{count}-{orientation.name.lower()}.svg"
                 for count in (2, 32) for orientation in Orientation},
            )
            self.assertFalse((package_path / "samples").exists())
            # The default generator writes into the package-owned samples folder.
            plugin = get_package("TEST_ADDON")
            with patch(
                "components.renderer.packages.samples.discover_packages",
                return_value=(plugin,),
            ):
                default_paths = generate_all_samples()
            self.assertEqual(len(default_paths), 4)
            self.assertTrue(all(
                path.parent == package_path / "samples" and path.is_file()
                for path in default_paths
            ))

    def test_unknown_family_and_unsupported_variant_fail_clearly(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported package family"):
            get_package("NOT_INSTALLED")
        with self.assertRaisesRegex(ValueError, "Unsupported DIP pin count"):
            get_package("DIP").create_renderer(12)
        with _added_package():
            with self.assertRaisesRegex(ValueError, "Unsupported TEST_ADDON pin count"):
                get_package("TEST_ADDON").create_renderer(4)

    def test_duplicate_family_is_reported_instead_of_overriding_a_package(self) -> None:
        with _added_package("duplicate_family.py"):
            with self.assertRaisesRegex(ValueError, "Duplicate package family: DIP"):
                discover_packages()

    def test_invalid_plugin_and_nested_import_errors_are_not_hidden(self) -> None:
        for fixture, exception, message in (
            ("invalid_export.py", ValueError, "must export a PackagePlugin"),
            ("missing_dependency.py", ModuleNotFoundError,
             "missing_package_dependency"),
        ):
            with self.subTest(fixture=fixture), _added_package(fixture):
                with self.assertRaisesRegex(exception, message):
                    discover_packages()


if __name__ == "__main__":
    unittest.main()
