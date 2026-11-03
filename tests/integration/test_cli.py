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

"""Exercise rendering two orientations from one unchanged synthetic JSON fixture."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = _ROOT / "components" / "input" / "tests" / "fixtures" / "pinout-columns.json"
_SVG = "{http://www.w3.org/2000/svg}"


class CliTests(unittest.TestCase):
    """Validate CLI overrides, immutable source data, and actionable failures."""

    def test_same_json_generates_horizontal_and_vertical_outputs(self) -> None:
        original = _SOURCE.read_bytes()
        with TemporaryDirectory(prefix="ic render ") as directory:
            for orientation, size, options in (
                ("landscape", (1920, 1080), []),
                ("portrait", (1080, 1920),
                 ["--content-scale", "0.2", "--legend-columns", "2"]),
            ):
                with self.subTest(orientation=orientation):
                    output = Path(directory) / f"pinout-{orientation}.svg"
                    command = [
                        sys.executable, "-m", "components.input",
                        str(_SOURCE), str(output), "--orientation", orientation,
                        *options,
                    ]
                    result = subprocess.run(
                        command, cwd=_ROOT, capture_output=True, text=True,
                        timeout=30, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    root = ET.parse(output).getroot()
                    width, height = size
                    self.assertEqual(root.get("viewBox"), f"0 0 {width} {height}")
                    self.assertEqual(root.get("width"), str(width))
                    self.assertEqual(root.get("height"), str(height))
                    self.assertIsNotNone(root.find(
                        f".//{_SVG}g[@aria-label='EXAMPLE']"
                    ))
                    if orientation == "portrait":
                        drawing = root.find(f"{_SVG}g[@id='drawing']")
                        self.assertIn("scale(0.2)", drawing.get("transform"))
                        legend = root.find(f"{_SVG}g[@id='legend']")
                        columns = {box.get("x")
                                   for box in legend.findall(f"{_SVG}rect")}
                        self.assertEqual(len(columns), 2)
        self.assertEqual(_SOURCE.read_bytes(), original)

    def test_invalid_legend_columns_do_not_write_svg(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "invalid.svg"
            result = subprocess.run(
                [sys.executable, "-m", "components.input", str(_SOURCE), str(output),
                 "--legend-columns", "0"],
                cwd=_ROOT, capture_output=True, text=True, timeout=30, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Legend columns", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())

    def test_invalid_scale_exits_without_writing_svg(self) -> None:
        with TemporaryDirectory() as directory:
            output = Path(directory) / "invalid.svg"
            result = subprocess.run(
                [sys.executable, "-m", "components.input", str(_SOURCE), str(output),
                 "--content-scale", "0"],
                cwd=_ROOT, capture_output=True, text=True, timeout=30, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("Content scale", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
