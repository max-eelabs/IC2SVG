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

"""Verify a new DIP count can be added with one JSON asset and no code edits."""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from components.renderer.packages.dip import SUPPORTED_PIN_COUNTS


_ROOT = Path(__file__).resolve().parents[2]


class DipVariantTests(unittest.TestCase):
    """Protect declarative extension and reject invalid package data early."""

    def setUp(self) -> None:
        path = (
            _ROOT / "components" / "renderer" / "packages" / "dip" / "variants"
            / "dip28.json"
        )
        self.variant = json.loads(path.read_text(encoding="utf-8"))

    def test_new_variant_file_works_without_modifying_existing_code(self) -> None:
        count = max(SUPPORTED_PIN_COUNTS) + 2
        variant = deepcopy(self.variant)
        variant["pin_count"] = count
        variant["geometry_mm"]["length"] = 40.0
        variant["reference"]["body_length"] = {
            "inches": "1.575", "millimeters": "40.00",
        }
        variant["source"] = (
            "Synthetic integration fixture, not a physical specification."
        )
        with TemporaryDirectory() as directory:
            root = Path(directory)
            # Only this added JSON file differs from the production package code.
            shutil.copytree(
                _ROOT / "components", root / "components",
                ignore=shutil.ignore_patterns("__pycache__", "samples", "tests"),
            )
            path = (
                root / "components" / "renderer" / "packages" / "dip" / "variants"
                / f"dip{count}.json"
            )
            path.write_text(json.dumps(variant), encoding="utf-8")
            probe = root / "probe_dip_variant.py"
            shutil.copyfile(
                Path(__file__).with_name("fixtures") / probe.name, probe
            )
            result = subprocess.run(
                [sys.executable, str(probe), str(count)], cwd=root,
                capture_output=True, text=True, timeout=30, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = json.loads(result.stdout)
            self.assertIn(count, generated["counts"])
            self.assertEqual(generated["new_samples"],
                             [f"dip{count}-landscape.svg", f"dip{count}-portrait.svg"])
            self.assertEqual(generated["sizes"], ["0 0 1920 1080", "0 0 1080 1920"])


if __name__ == "__main__":
    unittest.main()
