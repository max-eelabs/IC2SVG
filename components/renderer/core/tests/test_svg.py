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

"""Verify portable SVG encoding and file serialization."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from components.renderer.core import SvgDocument


class SvgExportTests(unittest.TestCase):
    """Check that locale settings cannot change saved SVG bytes or text."""

    def test_utf8_export_is_independent_of_locale(self) -> None:
        document = SvgDocument((1920, 1080))
        with document.sheet_layer("caf\u00e9"):
            pass
        with TemporaryDirectory() as directory:
            path = Path(directory) / "example.svg"
            original = document.to_string().encode("utf-8")
            for encoding in ("cp1252", "utf-8", "ascii"):
                with self.subTest(encoding=encoding), patch(
                    "locale.getpreferredencoding", return_value=encoding
                ):
                    document.save(path)
                    saved = path.read_bytes()
                    self.assertTrue(saved.startswith(
                        b"<?xml version='1.0' encoding='utf-8'?>\n"
                    ))
                    self.assertNotIn(b"\r\n", saved)
                    self.assertEqual(saved, original)
                    root = ET.fromstring(saved)
                    label = root.find(
                        ".//{http://www.w3.org/2000/svg}g[@id]"
                    )
                    self.assertEqual(label.get("id"), "caf\u00e9")


if __name__ == "__main__":
    unittest.main()
