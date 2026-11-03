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

"""Validate JSON contracts, category styles, and explicit sparse columns."""

from copy import deepcopy
from importlib.resources import files
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from jsonschema import Draft202012Validator

from components.input import load_input, parse_input
from components.renderer import Orientation


_FIXTURES = Path(__file__).with_name("fixtures")


class JsonInputTests(unittest.TestCase):
    """Check structural schema and cross-field validation independently."""

    def setUp(self) -> None:
        self.data = json.loads(
            (_FIXTURES / "pinout-columns.json").read_text(encoding="utf-8")
        )

    def test_schema_and_fixture(self) -> None:
        schema = json.loads(files("components.input").joinpath("schema.json")
                            .read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        parsed = load_input(_FIXTURES / "pinout-columns.json")
        self.assertEqual(parsed.pin_count, 8)
        self.assertIn("<svg", parsed.render().to_string())
        self.assertEqual(parsed.render().to_string(), parsed.render().to_string())

    def test_defaults_colors_and_order(self) -> None:
        self.data.pop("orientation")
        self.data["categories"]["power"].pop("color")
        parsed = parse_input(self.data)
        definitions = dict(parsed.definitions)
        self.assertEqual(parsed.orientation, Orientation.LANDSCAPE)
        self.assertEqual(parsed.content_scale, 0.6)
        self.assertEqual(definitions[1][0].label.color, "#E53935")
        self.assertEqual(definitions[4][0].label.text_color, "#FFFFFF")
        self.data["pins"].reverse()
        for pin in self.data["pins"]:
            pin["definitions"].reverse()
        self.data["categories"] = dict(reversed(list(self.data["categories"].items())))
        self.assertEqual(parsed, parse_input(self.data))
        self.assertEqual(parsed.render().to_string(), parse_input(self.data).render()
                         .to_string())

    def test_invalid_structure(self) -> None:
        cases = [
            ("empty name", lambda data: data.update(name="  ")),
            ("unsupported package", lambda data: data["package"].update(family="QFN")),
            ("unsupported count", lambda data: data["package"].update(pin_count=12)),
            ("float count", lambda data: data["package"].update(pin_count=8.0)),
            ("unknown field", lambda data: data.update(typo=True)),
            ("bad color", lambda data: data["categories"]["power"].update(color="red")),
            ("nonfinite scale", lambda data: data.update(content_scale=float("nan"))),
            ("empty comment", lambda data: data.update(comments=["   "])),
            ("invalid comments", lambda data: data.update(comments="text")),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                data = deepcopy(self.data)
                mutate(data)
                with self.assertRaises(ValueError):
                    parse_input(data)

    def test_cross_field_errors(self) -> None:
        missing = deepcopy(self.data)
        missing["pins"].pop()
        duplicate = deepcopy(self.data)
        duplicate["pins"][-1]["number"] = 1
        unknown = deepcopy(self.data)
        unknown["pins"][0]["definitions"][0]["category"] = "absent"
        column = deepcopy(self.data)
        column["pins"][1]["definitions"][1]["column"] = 1
        outside = deepcopy(self.data)
        outside["pins"][0]["number"] = 9
        for data in (missing, duplicate, unknown, column, outside):
            with self.subTest(data=data), self.assertRaises(ValueError):
                parse_input(data)

    def test_custom_category_and_explicit_foreground(self) -> None:
        self.data["categories"]["custom"] = {
            "name": "Custom function", "text_color": "#123456"
        }
        self.data["pins"][0]["definitions"][0]["category"] = "custom"
        label = dict(parse_input(self.data).definitions)[1][0].label
        self.assertEqual(label.color, "#E0E0E0")
        self.assertEqual(label.text_color, "#123456")

    def test_definition_colors_override_category_defaults(self) -> None:
        parsed = parse_input(self.data)
        definitions = dict(parsed.definitions)
        self.assertEqual(definitions[1][0].label.color, "#E53935")
        self.assertEqual(definitions[4][0].label.color, "#202020")
        self.assertEqual(definitions[4][0].label.text_color, "#FFFFFF")
        power = [entry for entry in parsed.legend if entry.description == "Power"]
        self.assertEqual(len(power), 1)
        self.assertEqual(power[0].sample.text, "VCC")
        self.assertEqual(power[0].variants[0].text, "GND")
        self.assertEqual(power[0].swatch.text, "VCC/GND")

        self.data["categories"]["power"]["text_color"] = "#123456"
        ground = self.data["pins"][3]["definitions"][0]
        ground["text_color"] = "#FFFFFF"
        definitions = dict(parse_input(self.data).definitions)
        self.assertEqual(definitions[1][0].label.text_color, "#123456")
        self.assertEqual(definitions[4][0].label.text_color, "#FFFFFF")
        ground["color"] = "not-a-color"
        with self.assertRaises(ValueError):
            parse_input(self.data)

    def test_all_supported_packages_load(self) -> None:
        for count in (4, 6, 8, 14, 16, 18, 20, 24, 28):
            with self.subTest(count=count):
                data = deepcopy(self.data)
                data["package"]["pin_count"] = count
                data["pins"] = [
                    {"number": number, "type": "nc", "definitions": []}
                    for number in range(1, count + 1)
                ]
                parsed = parse_input(data)
                self.assertEqual(len(parsed.definitions), count)
                parsed.render()

    def test_duplicate_object_keys(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"name":"A","name":"B"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                load_input(path)


if __name__ == "__main__":
    unittest.main()
