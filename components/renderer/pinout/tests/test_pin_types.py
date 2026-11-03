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

"""Validate required electrical roles and their first-position neutral badges."""

from copy import deepcopy
from dataclasses import replace
from importlib.resources import files
import json
import unittest
from xml.etree import ElementTree as ET

from jsonschema import Draft202012Validator

from components.input import parse_input
from components.renderer import (
    DipRenderer, Orientation, PinDefinition, PinLabel, PinoutRenderer, PinType,
)


_SVG = "{http://www.w3.org/2000/svg}"


def _annotation_boxes(svg: str) -> list[tuple[str, ET.Element, ET.Element]]:
    """Pair each annotation's background box with its following text group."""
    root = ET.fromstring(svg)
    drawing = root.find(f"{_SVG}g[@id='drawing']")
    children = list(root if drawing is None else drawing)
    return [
        (text.get("aria-label"), box, text)
        for box, text in zip(children, children[1:])
        if box.tag == f"{_SVG}rect" and text.tag == f"{_SVG}g"
        and text.get("aria-label") is not None
    ]


class PinTypeTests(unittest.TestCase):
    """Protect schema requirements, physical ordering, styles, and input ownership."""

    def setUp(self) -> None:
        self.data = {
            "name": "TYPES",
            "package": {"family": "DIP", "pin_count": 6},
            "categories": {"signal": {"name": "Signal", "color": "#ABCDEF"}},
            "pins": [
                {"number": number, "type": role, "definitions": [
                    {"column": 1, "category": "signal", "name": f"F{number}"}
                ]}
                for number, role in enumerate(
                    ("input", "output", "io", "power", "nc", "io"), start=1
                )
            ],
        }

    def test_schema_requires_one_valid_role_per_pin(self) -> None:
        schema = json.loads(
            files("components.input").joinpath("schema.json")
            .read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(schema)
        self.assertTrue(validator.is_valid(self.data))
        invalid_roles = (None, "", "Input", "analog", "in", 1, {}, ["io"])
        for role in invalid_roles:
            with self.subTest(role=role):
                data = deepcopy(self.data)
                data["pins"][0]["type"] = role
                self.assertFalse(validator.is_valid(data))
                with self.assertRaisesRegex(ValueError, "pins.0.type"):
                    parse_input(data)
        del self.data["pins"][0]["type"]
        self.assertFalse(validator.is_valid(self.data))
        with self.assertRaisesRegex(ValueError, "type.*required"):
            parse_input(self.data)

    def test_badge_is_first_on_both_sides_with_fixed_colors(self) -> None:
        original = deepcopy(self.data)
        parsed = parse_input(self.data)
        self.assertEqual(dict(parsed.pin_types)[4], PinType.POWER)
        self.assertEqual(dict(parsed.definitions)[1][0].column, 1)
        self.assertEqual([entry.description for entry in parsed.legend], ["Signal"])
        for orientation in Orientation:
            configured = replace(parsed, orientation=orientation, content_scale=0.4)
            svg = configured.render().to_string()
            boxes = _annotation_boxes(svg)
            badges = [item for item in boxes if item[1].get("fill") == "#EEEEEE"]
            self.assertEqual([item[0] for item in badges],
                             ["IN", "OUT", "I/O", "PWR", "NC", "I/O"])
            functions = {label: box for label, box, _ in boxes if label.startswith("F")}
            for number, (_, badge, text) in enumerate(badges, start=1):
                self.assertEqual(text.get("fill"), "#555555")
                function = functions[f"F{number}"]
                self.assertEqual(function.get("fill"), "#ABCDEF")
                self.assertEqual(function.get("y"), badge.get("y"))
                if number <= 3:
                    self.assertLess(
                        float(function.get("x")) + float(function.get("width")),
                        float(badge.get("x")),
                    )
                else:
                    self.assertGreater(
                        float(function.get("x")),
                        float(badge.get("x")) + float(badge.get("width")),
                    )
            self.assertEqual(svg, configured.render().to_string())
        self.assertEqual(self.data, original)

    def test_nc_without_functions_or_categories_still_renders(self) -> None:
        self.data["categories"] = {}
        for pin in self.data["pins"]:
            pin["type"] = "nc"
            pin["definitions"] = []
        parsed = parse_input(self.data)
        self.assertEqual(parsed.legend, ())
        badges = _annotation_boxes(parsed.render().to_string())
        self.assertEqual([label for label, _, _ in badges], ["NC"] * 6)
        self.data["pins"][3].pop("type")
        with self.assertRaisesRegex(ValueError, "type.*required"):
            parse_input(self.data)

    def test_function_column_16_remains_available_after_type_badge(self) -> None:
        self.data["content_scale"] = 0.1
        self.data["pins"][0]["definitions"][0]["column"] = 16
        parsed = parse_input(self.data)
        self.assertEqual(dict(parsed.definitions)[1][0].column, 16)
        boxes = _annotation_boxes(parsed.render().to_string())
        badge = next(box for label, box, _ in boxes if label == "IN")
        function = next(box for label, box, _ in boxes if label == "F1")
        self.assertLess(float(function.get("x")), float(badge.get("x")))

    def test_sparse_function_columns_stay_aligned_after_badges(self) -> None:
        self.data["pins"][0]["definitions"][0]["column"] = 2
        self.data["pins"][1]["definitions"][0]["column"] = 2
        self.data["pins"][4]["definitions"][0]["column"] = 2
        self.data["pins"][5]["definitions"][0]["column"] = 2
        boxes = {
            label: box for label, box, _ in
            _annotation_boxes(parse_input(self.data).render().to_string())
        }
        self.assertEqual(boxes["F1"].get("x"), boxes["F2"].get("x"))
        self.assertEqual(boxes["F5"].get("x"), boxes["F6"].get("x"))
        self.assertLess(float(boxes["F1"].get("x")), float(boxes["F3"].get("x")))
        self.assertGreater(float(boxes["F5"].get("x")), float(boxes["F4"].get("x")))

    def test_python_roles_require_a_complete_valid_mapping(self) -> None:
        renderer = PinoutRenderer(DipRenderer(4))
        roles = dict.fromkeys(range(1, 5), PinType.IO)
        original = dict(roles)
        labels = {1: [PinDefinition(1, PinLabel("SIGNAL"))]}
        renderer.render("TEST", labels, pin_types=roles)
        self.assertEqual(roles, original)
        self.assertEqual(labels[1][0].column, 1)
        for invalid in ({1: PinType.IO}, {**roles, 5: PinType.NC}):
            with self.assertRaisesRegex(ValueError, "every physical pin"):
                renderer.render("TEST", pin_types=invalid)
        with self.assertRaisesRegex(TypeError, "PinType"):
            renderer.render("TEST", pin_types={**roles, 1: "io"})
        with self.assertRaisesRegex(TypeError, "integer"):
            renderer.render("TEST", pin_types={**roles, "1": PinType.IO})

    def test_all_package_sizes_fit_badges_without_functions(self) -> None:
        for count in (4, 6, 8, 14, 16, 18, 20, 24, 28):
            for orientation in Orientation:
                with self.subTest(pin_count=count, orientation=orientation):
                    roles = dict.fromkeys(range(1, count + 1), PinType.NC)
                    svg = PinoutRenderer(DipRenderer(count)).render(
                        "TEST", orientation=orientation, pin_types=roles
                    ).to_string()
                    self.assertEqual(len(_annotation_boxes(svg)), count)


if __name__ == "__main__":
    unittest.main()
