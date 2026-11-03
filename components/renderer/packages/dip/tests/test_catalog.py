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

"""Validate package-owned DIP variant data before rendering."""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from components.renderer.packages.dip.catalog import load_variants


class DipCatalogTests(unittest.TestCase):
    """Reject invalid geometry, missing references, and ambiguous variant catalogs."""

    def setUp(self) -> None:
        path = Path(__file__).resolve().parents[1] / "variants" / "dip28.json"
        self.variant = json.loads(path.read_text(encoding="utf-8"))

    def test_invalid_and_inconsistent_variant_data_is_rejected(self) -> None:
        variants = []
        for field, value in (("span", 1), ("pitch", 0), ("width", float("inf"))):
            variant = deepcopy(self.variant)
            variant["geometry_mm"][field] = value
            variants.append(variant)
        missing_units = deepcopy(self.variant)
        del missing_units["reference"]["body_width"]["inches"]
        variants.append(missing_units)
        odd_count = deepcopy(self.variant)
        odd_count["pin_count"] = 9
        variants.append(odd_count)
        for variant in variants:
            with self.subTest(variant=variant), TemporaryDirectory() as directory:
                path = Path(directory) / "variant.json"
                path.write_text(json.dumps(variant), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_variants(directory)

    def test_duplicate_counts_and_empty_catalog_are_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "No DIP variant"):
                load_variants(directory)
            for name in ("first.json", "second.json"):
                (Path(directory) / name).write_text(
                    json.dumps(self.variant), encoding="utf-8"
                )
            with self.assertRaisesRegex(ValueError, "duplicate DIP pin count"):
                load_variants(directory)


if __name__ == "__main__":
    unittest.main()
